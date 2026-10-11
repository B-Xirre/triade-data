"""Run current and frozen historical tests with a bounded workspace temp root."""
from pathlib import Path
import json,os,tempfile,unittest
root=Path(__file__).resolve().parents[1]
task_temp=root/'.test-tmp';task_temp.mkdir(exist_ok=True)
tempfile.tempdir=str(task_temp.resolve())
suite=unittest.defaultTestLoader.discover(str(root/'tests'))
result=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped)}))
raise SystemExit(0 if result.wasSuccessful() else 1)
