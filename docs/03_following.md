
# Following algorithm

unity 경로 설정
- `utils/baseline_trainer.py` 에서 `class Policy` 의 `__init__` 에서 `if self.u_model:` 밑에 코드에서 `name` 에 경로 설정 (line 63)

---

학습 시
1. `utils/SAC_config.json` 에서 `"inference_mode" : "False"` 로 설정 (line 104)
2. `utils/SAC_config.json` 에서 `"load_model" : "False"` 로 설정 (line 96)
3. `utils/SAC_Trainer.py` 에서 `run` 함수안의 `env_config  "followingMode": 0` 으로 설정 (line 444)
4. `python SAC_following.py` 실행

---

following task 수행 시
1. `utils/SAC_config.json` 에서 `"inference_mode" : "True"` 로 설정 (line 104)
2. `utils/SAC_config.json` 에서 `"load_model" : "True"` 로 설정 (line 96)
3. `utils/SAC_config.json` 에서 `"load_path"` 에 모델 경로 설정 (line 97)
4. `utils/SAC_Trainer.py` 에서 `run` 함수안의 `env_config  "followingMode": 1` 로 설정 (line 444)
5. `python SAC_following.py` 실행