from django.db import models
import subprocess

CURRENT_GIT_REVISION_INFO = None

class GitRevisionManager(models.Manager):
    def capture(self):
        """
        Capture current git revision from the current working directory. If
        revision cannot be obtained, return null. The revision is not saved to
        database.
        """
        rev = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True)
        diff = subprocess.run(["git", "diff"], capture_output=True)
        if rev.returncode != 0 or diff.returncode != 0:
            print("Cannot capture git revision")
            print(f"rev stderr: {rev.stderr}")
            print(f"diff stderr: {diff.stderr}")
            return None
        return GitRevision(rev=rev.stdout.decode("utf-8").strip(),
                           diff=diff.stdout.decode("utf-8").strip())

    def getCurrent(self):
        global CURRENT_GIT_REVISION_INFO
        if CURRENT_GIT_REVISION_INFO is not None:
            return CURRENT_GIT_REVISION_INFO
        try:
            lastCaptured = self.latest("id")
            current = self.capture()
            if lastCaptured.rev == current.rev and lastCaptured.diff == current.diff:
                CURRENT_GIT_REVISION_INFO = lastCaptured
                return lastCaptured
        except GitRevision.DoesNotExist:
            current = self.capture()
        current.save()
        CURRENT_GIT_REVISION_INFO = current
        return current

class GitRevision(models.Model):
    rev = models.CharField(max_length=40)
    diff = models.TextField()

    objects = GitRevisionManager()

