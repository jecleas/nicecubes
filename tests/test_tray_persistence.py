import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta

from app import create_app
from app.db import init_db


class TrayPersistenceTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, 'data', 'app.sqlite')
        self.app = self._make_app(self.db_path)
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def _make_app(self, db_path):
        return create_app({
            'TESTING': True,
            'SECRET_KEY': 'test',
            'DATABASE': db_path,
        })

    def _login(self, client, name='Ada'):
        response = client.post('/api/auth/login', json={'name': name})
        self.assertEqual(response.status_code, 200)
        return response

    def _stats(self, db_path, username):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            '''
            SELECT s.cubes_created, s.cubes_frozen, s.trays_frozen
            FROM user_stats s
            JOIN user u ON u.id = s.user_id
            WHERE u.username = ?
            ''',
            (username,),
        ).fetchone()
        conn.close()
        return row

    def test_database_directory_is_created_on_first_boot(self):
        db_path = os.path.join(self.tmp.name, 'first-boot', 'data', 'app.sqlite')
        self.assertFalse(os.path.exists(os.path.dirname(db_path)))

        self._make_app(db_path)

        self.assertTrue(os.path.isdir(os.path.dirname(db_path)))
        self.assertTrue(os.path.isfile(db_path))

        conn = sqlite3.connect(db_path)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        tray_ids = [row[0] for row in conn.execute('SELECT id FROM tray_state ORDER BY id')]
        conn.close()

        self.assertIn('user', tables)
        self.assertIn('user_stats', tables)
        self.assertIn('tray_state', tables)
        self.assertEqual(tray_ids, ['tray1', 'tray2'])

    def test_tray_contents_survive_a_new_process(self):
        self._login(self.client)
        toggled = self.client.post(
            '/api/toggle-cube',
            json={'trayId': 'tray1', 'cubeIndex': 3},
        )
        self.assertEqual(toggled.status_code, 200)
        self.assertEqual(toggled.get_json()['active_cubes'], [3])

        toggled_again = self.client.post(
            '/api/toggle-cube',
            json={'trayId': 'tray1', 'cubeIndex': 7},
        )
        self.assertEqual(toggled_again.get_json()['active_cubes'], [3, 7])

        removed = self.client.post(
            '/api/toggle-cube',
            json={'trayId': 'tray1', 'cubeIndex': 3},
        )
        self.assertEqual(removed.get_json()['active_cubes'], [7])

        frozen = self.client.post('/api/freeze-tray', json={'trayId': 'tray1'})
        self.assertEqual(frozen.status_code, 200)
        frozen_body = frozen.get_json()
        self.assertTrue(frozen_body['is_frozen'])
        self.assertEqual(frozen_body['active_cubes'], [7])
        self.assertEqual(
            datetime.fromisoformat(frozen_body['expires_at'])
            - datetime.fromisoformat(frozen_body['frozen_at']),
            timedelta(hours=4),
        )

        # Same as a Fly machine stop/start or a redeploy: new process, same file.
        restarted = self._make_app(self.db_path).test_client()
        states = restarted.get('/api/tray-states')
        self.assertEqual(states.status_code, 200)
        tray1 = states.get_json()['tray1']
        tray2 = states.get_json()['tray2']

        self.assertEqual(tray1['active_cubes'], [7])
        self.assertTrue(tray1['is_frozen'])
        self.assertEqual(tray1['frozen_at'], frozen_body['frozen_at'])
        self.assertEqual(tray1['expires_at'], frozen_body['expires_at'])
        self.assertEqual(tray1['revision'], frozen_body['revision'])
        self.assertEqual(tray2['active_cubes'], [])
        self.assertFalse(tray2['is_frozen'])

        stats = self._stats(self.db_path, 'Ada')
        self.assertEqual(stats['cubes_created'], 2)
        self.assertEqual(stats['cubes_frozen'], 1)
        self.assertEqual(stats['trays_frozen'], 1)

    def test_expired_freeze_is_cleared_and_stays_cleared(self):
        self._login(self.client)
        self.client.post('/api/toggle-cube', json={'trayId': 'tray2', 'cubeIndex': 1})
        frozen = self.client.post('/api/freeze-tray', json={'trayId': 'tray2'})
        revision_while_frozen = frozen.get_json()['revision']

        past = (datetime.now() - timedelta(minutes=5)).isoformat()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            '''
            UPDATE tray_state
            SET is_frozen = 1, frozen_at = ?, expires_at = ?
            WHERE id = ?
            ''',
            (past, past, 'tray2'),
        )
        conn.commit()
        conn.close()

        states = self.client.get('/api/tray-states')
        tray2 = states.get_json()['tray2']
        self.assertFalse(tray2['is_frozen'])
        self.assertIsNone(tray2['frozen_at'])
        self.assertIsNone(tray2['expires_at'])
        self.assertEqual(tray2['active_cubes'], [1])
        self.assertGreater(tray2['revision'], revision_while_frozen)

        restarted = self._make_app(self.db_path).test_client()
        again = restarted.get('/api/tray-states').get_json()['tray2']
        self.assertEqual(again['revision'], tray2['revision'])
        self.assertFalse(again['is_frozen'])
        self.assertEqual(again['active_cubes'], [1])

    def test_frozen_tray_ignores_further_toggles(self):
        self._login(self.client)
        self.client.post('/api/toggle-cube', json={'trayId': 'tray1', 'cubeIndex': 0})
        self.client.post('/api/freeze-tray', json={'trayId': 'tray1'})

        toggled = self.client.post(
            '/api/toggle-cube',
            json={'trayId': 'tray1', 'cubeIndex': 1},
        )
        self.assertEqual(toggled.get_json()['active_cubes'], [0])
        self.assertTrue(toggled.get_json()['is_frozen'])

    def test_toggle_requires_login_and_known_tray(self):
        anonymous = self.client.post(
            '/api/toggle-cube',
            json={'trayId': 'tray1', 'cubeIndex': 0},
        )
        self.assertEqual(anonymous.status_code, 401)

        self._login(self.client)
        unknown = self.client.post(
            '/api/toggle-cube',
            json={'trayId': 'tray9', 'cubeIndex': 0},
        )
        self.assertEqual(unknown.status_code, 404)

    def test_existing_user_database_gains_trays_without_losing_rows(self):
        legacy_path = os.path.join(self.tmp.name, 'legacy', 'app.sqlite')
        os.makedirs(os.path.dirname(legacy_path))
        conn = sqlite3.connect(legacy_path)
        conn.executescript(
            '''
            CREATE TABLE user (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE NOT NULL,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE user_stats (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER UNIQUE NOT NULL,
              cubes_created INTEGER NOT NULL DEFAULT 0,
              cubes_frozen INTEGER NOT NULL DEFAULT 0,
              trays_frozen INTEGER NOT NULL DEFAULT 0,
              FOREIGN KEY (user_id) REFERENCES user (id)
            );
            INSERT INTO user (username) VALUES ('Ada');
            INSERT INTO user_stats (user_id, cubes_created, cubes_frozen, trays_frozen)
            VALUES (1, 4, 2, 1);
            '''
        )
        conn.commit()
        conn.close()

        create_app({
            'TESTING': True,
            'SECRET_KEY': 'test',
            'DATABASE': legacy_path,
        })

        conn = sqlite3.connect(legacy_path)
        conn.row_factory = sqlite3.Row
        user = conn.execute('SELECT username FROM user').fetchone()
        stats = conn.execute(
            'SELECT cubes_created, cubes_frozen, trays_frozen FROM user_stats'
        ).fetchone()
        trays = [row[0] for row in conn.execute('SELECT id FROM tray_state ORDER BY id')]
        conn.close()

        self.assertEqual(user['username'], 'Ada')
        self.assertEqual(tuple(stats), (4, 2, 1))
        self.assertEqual(trays, ['tray1', 'tray2'])

    def test_init_db_command_resets_trays_and_users(self):
        self._login(self.client, name='Ada')
        self.client.post('/api/toggle-cube', json={'trayId': 'tray1', 'cubeIndex': 2})

        with self.app.app_context():
            init_db()

        conn = sqlite3.connect(self.db_path)
        users = conn.execute('SELECT COUNT(*) FROM user').fetchone()[0]
        cubes = conn.execute(
            'SELECT active_cubes, is_frozen, revision FROM tray_state WHERE id = ?',
            ('tray1',),
        ).fetchone()
        conn.close()

        self.assertEqual(users, 0)
        self.assertEqual(cubes, ('[]', 0, 0))

    def test_default_database_is_the_instance_file(self):
        previous = os.environ.pop('DATABASE_PATH', None)
        try:
            app = create_app({'TESTING': True, 'SECRET_KEY': 'test'})
        finally:
            if previous is not None:
                os.environ['DATABASE_PATH'] = previous

        self.assertTrue(app.config['DATABASE'].endswith(os.path.join('instance', 'app.sqlite')))
        self.assertTrue(os.path.isfile(app.config['DATABASE']))
        conn = sqlite3.connect(app.config['DATABASE'])
        tray_ids = [row[0] for row in conn.execute('SELECT id FROM tray_state ORDER BY id')]
        conn.close()
        self.assertEqual(tray_ids, ['tray1', 'tray2'])


if __name__ == '__main__':
    unittest.main()
