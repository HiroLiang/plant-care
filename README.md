# Plant-Care System

---

## Start Up

- monitor-daemon

```shell
# 1. git clone
git clone https://github.com/HiroLiang/plant-care.git

# 2. build python venv
python3 -m venv venv --system-site-packages

# 3. use venv
source venv/bin/activate

# * (leave venv)
deactivate

# 4. install from requirements
pip install -r requirements.txt

# 5. use SHT31 (optional)
pip install adafruit-circuitpython-sht31d

# 6. start system (mock test)
make dev

# (use SHT31)
PYTHONPATH=src \
HTTP_HOST=0.0.0.0 \
HTTP_PORT=8001 \
SENSOR_BACKEND=rasp \
.venv/bin/python src/main.py
```