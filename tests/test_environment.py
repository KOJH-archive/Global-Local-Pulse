from services.environment import load_environment

def test_env_from_project_not_cwd(tmp_path,monkeypatch):
 monkeypatch.delenv('OPENAI_API_KEY',raising=False)
 root=tmp_path/'project';root.mkdir();(root/'.env').write_text('OPENAI_API_KEY=test-fixture-only\n')
 other=tmp_path/'other';other.mkdir();monkeypatch.chdir(other)
 load_environment(root)
 import os
 assert os.getenv('OPENAI_API_KEY')=='test-fixture-only'

def test_server_env_takes_priority(tmp_path,monkeypatch):
 monkeypatch.setenv('OPENAI_API_KEY','server-fixture')
 (tmp_path/'.env').write_text('OPENAI_API_KEY=file-fixture\n')
 load_environment(tmp_path)
 import os
 assert os.getenv('OPENAI_API_KEY')=='server-fixture'
