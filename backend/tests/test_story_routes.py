import unittest

from fastapi.testclient import TestClient

from backend.db.database import SessionLocal, create_tables
from backend.main import app
from backend.models.job import StoryJob
from backend.models.story import Story, StoryNode


class StoryRouteTests(unittest.TestCase):
    def setUp(self):
        create_tables()
        self.client = TestClient(app)
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_complete_story_by_job_returns_409_when_story_still_processing(self):
        job = StoryJob(job_id="job-123", session_id="session-123", theme="fantasy", status="processing")
        self.db.add(job)
        self.db.commit()

        response = self.client.get("/api/story/job/job-123/complete")

        self.assertEqual(response.status_code, 409)
        self.assertIn("still in progress", response.json()["detail"])

    def test_complete_story_by_job_returns_story_when_finished(self):
        job = StoryJob(job_id="job-456", session_id="session-456", theme="fantasy", status="completed", story_id=2)
        self.db.add(job)
        self.db.commit()

        story = Story(title="Demo", session_id="session-456")
        self.db.add(story)
        self.db.commit()
        self.db.refresh(story)

        root = StoryNode(story_id=story.id, content="root", is_root=True, is_ending=False, is_winning_ending=False, options=[{"text": "next", "node_id": None}])
        self.db.add(root)
        self.db.commit()

        job.story_id = story.id
        self.db.add(job)
        self.db.commit()

        response = self.client.get("/api/story/job/job-456/complete")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "demo")


if __name__ == "__main__":
    unittest.main()
