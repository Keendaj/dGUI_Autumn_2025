#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template_string, send_from_directory, abort
import os
import json

try:
    from core import FarmLabyrinth, RobotFarmer, DirectionType, FarmCellType
except Exception as e:
    raise RuntimeError(f"Failed to import core.py: {e}")

app = Flask(__name__)

lab = FarmLabyrinth(width=10, height=10)
lab.initialize(FarmCellType.Greenhouse)
robot = RobotFarmer(lab)
robot.place(0, lab.height - 1)

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')

def serialize_state(labyrinth, robot_obj):
    cells = []
    for y in range(labyrinth.height):
        row = []
        for x in range(labyrinth.width):
            cell = labyrinth.get_cell(x, y)
            row.append({
                'cell_type': int(cell.cell_type.value),
                'has_robot': bool(cell.has_robot),
            })
        cells.append(row)
    return {
        'width': labyrinth.width,
        'height': labyrinth.height,
        'cells': cells,
        'robot': {
            'x': robot_obj.current_cell.x if robot_obj.current_cell else None,
            'y': robot_obj.current_cell.y if robot_obj.current_cell else None,
        }
    }

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/assets/<path:filename>')
def assets(filename):
    if not os.path.exists(os.path.join(ASSETS_DIR, filename)):
        abort(404)
    return send_from_directory(ASSETS_DIR, filename)

@app.route('/api/state', methods=['GET'])
def api_state():
    return jsonify(serialize_state(lab, robot))

@app.route('/api/export', methods=['GET'])
def api_export():
    try:
        code = robot.encode_state()
        return jsonify({'code': code})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/import', methods=['POST'])
def api_import():
    data = request.json or {}
    code = data.get('code', '')
    try:
        robot.decode_state(code)
        return jsonify({'ok': True, 'state': serialize_state(lab, robot)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/execute', methods=['POST'])
def api_execute():
    data = request.json or {}
    commands = data.get('commands', [])
    if not isinstance(commands, list):
        return jsonify({'error': 'commands must be a list'}), 400

    try:
        initial_code = robot.encode_state()
    except Exception:
        initial_code = None

    frames = []
    for idx, cmd in enumerate(commands):
        cmd = cmd.strip()
        result = None
        msg = ''
        try:
            if cmd == 'Вправо':
                result = robot.move_right()
                msg = 'robot crashed'
            elif cmd == 'Влево':
                result = robot.move_left()
                msg = 'robot crashed'
            elif cmd == 'Вверх':
                result = robot.move_previous_row()
                msg = 'robot crashed'
            elif cmd == 'Вниз':
                result = robot.move_next_row()
                msg = 'robot crashed'
            elif cmd == 'ВлевоВверх':
                result = robot.move_up()
                msg = 'robot crashed'
            elif cmd == 'ВправоВниз':
                result = robot.move_down()
                msg = 'robot crashed'
            elif cmd == 'Грядка':
                result = robot.action_soil()
                msg = 'wrong action'
            elif cmd == 'Посадка':
                result = robot.action_garden()
                msg = 'wrong action'
            else:
                return jsonify({'error': f'Unknown command: {cmd}'}), 400
        except Exception as e:
            if initial_code is not None:
                try:
                    robot.decode_state(initial_code)
                except Exception:
                    pass
            return jsonify({'error': str(e)}), 500

        if result is None:
            # Action had no effect (invalid move/action) — record current
            # state as a frame and continue executing remaining commands.
            frames.append(serialize_state(lab, robot))
            continue

        frames.append(serialize_state(lab, robot))

    victory = False
    if robot.current_cell and robot.current_cell.cell_type == FarmCellType.Finish:
        all_harvested = True
        for cell in lab.get_iterator():
            if cell.cell_type in (FarmCellType.Soil, FarmCellType.Garden):
                all_harvested = False
                break
        if all_harvested:
            victory = True

    message = ''
    if not victory:
        if not robot.current_cell:
            message = 'Робот не находится на поле.'
        elif robot.current_cell.cell_type != FarmCellType.Finish:
            message = 'Уровень не пройден: робот не добрался до финиша.'
        else:
            message = 'Уровень не пройден: остались почва или грядки.'

    if initial_code is not None:
        try:
            robot.decode_state(initial_code)
        except Exception:
            pass

    return jsonify({'frames': frames, 'victory': victory, 'message': message})

@app.route('/api/place', methods=['POST'])
def api_place():
    data = request.json or {}
    x = data.get('x')
    y = data.get('y')
    try:
        ok = robot.place(int(x), int(y))
        if not ok:
            return jsonify({'error': 'invalid coords'}), 400
        return jsonify({'ok': True, 'state': serialize_state(lab, robot)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/toggle_cell', methods=['POST'])
def api_toggle_cell():
    data = request.json or {}
    x = int(data.get('x'))
    y = int(data.get('y'))
    try:
        cell = lab.get_cell(x, y)
        if not cell:
            return jsonify({'error': 'Invalid coords'}), 400
        new_type = (cell.cell_type.value + 1) % 7
        lab.place_cell(x, y, new_type)
        return jsonify({'ok': True, 'state': serialize_state(lab, robot)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


HTML = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>RoboFarm</title>
<style>
body { font-family: Arial; margin: 10px; }
#app { display: flex; gap: 15px; }
#left { width: 280px; }
textarea { width: 100%; height: 200px; }
canvas { border: 1px solid #333; }
button { padding: 8px 12px; margin: 3px; }
.modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); }
.modal-content { background: white; margin: 5% auto; padding: 20px; width: 500px; max-height: 80%; overflow-y: auto; border-radius: 5px; }
.close { float: right; font-size: 24px; cursor: pointer; }
</style>
</head>
<body>
<h1>РобоФерма</h1>
<button onclick="showMenu('help')">Справка: Команды</button>
<button onclick="showMenu('guide')">Справка: Руководство</button>

<div id="helpModal" class="modal">
<div class="modal-content">
<span class="close" onclick="closeModal('helpModal')">&times;</span>
<h2>Команды робота</h2>
<pre>
Вправо — перемещение вправо
Влево — перемещение влево
Вверх — перемещение на следующую строку вверх
Вниз — перемещение на следующую строку вниз
ВлевоВверх — диагональное перемещение вверх-влево
ВправоВниз — диагональное перемещение вниз-вправо
Грядка — превратить почву в грядку
Посадка — вырастить растение в грядке
</pre>
</div>
</div>

<div id="guideModal" class="modal">
<div class="modal-content">
<span class="close" onclick="closeModal('guideModal')">&times;</span>
<h2>Руководство</h2>
<p>Цель: засадить всю почву растениями и добраться до финиша.</p>
<p>Клик по клетке меняет её тип. Shift+Клик перемещает робота.</p>
</div>
</div>

<div id="app">
<div id="left">
<label>Код команд:</label>
<textarea id="commands"></textarea>
<button id="copy">Скопировать</button>
<button id="paste">Вставить</button>
<button id="run">Выполнить</button>
<button id="export">Экспорт уровня</button>
<button id="import">Импорт уровня</button>
</div>
<canvas id="board"></canvas>
</div>

<script>
const assetNames = {0:'Soil.png',1:'Garden.png',2:'Harvest.png',3:'Greenhouse.png',4:'Water.png',5:'Barrier.png',6:'Finish.png'};
const assets = {};
let assetsLoaded = false;
let state = null;
let CELL = 40;
let board, ctx;

async function loadAssets() {
  const promises = [];
  for (const [k, f] of Object.entries(assetNames)) {
        const img = new Image();
        // add debug handlers
        (function(filename){
            img.onload = function(){ console.log('[ASSET] loaded:', filename); };
            img.onerror = function(e){ console.error('[ASSET] failed to load:', filename, e); };
        })(f);
        img.src = '/assets/' + f;
        assets[k] = img;
        // create promise that resolves when image finished (either load or error)
        promises.push(new Promise(function(res){ img.addEventListener('load', res); img.addEventListener('error', res); }));
  }
  const r = new Image();
    // robot image with debug handlers
    (function(filename){
        r.onload = function(){ console.log('[ASSET] loaded:', filename); };
        r.onerror = function(e){ console.error('[ASSET] failed to load:', filename, e); };
    })('Robot.png');
    r.src = '/assets/Robot.png';
    assets['robot'] = r;
    promises.push(new Promise(function(res){ r.addEventListener('load', res); r.addEventListener('error', res); }));
  await Promise.all(promises);
  assetsLoaded = true;
}

async function loadState() {
  const r = await fetch('/api/state');
  state = await r.json();
  CELL = Math.max(16, Math.min(64, Math.floor((window.innerWidth-320)/state.width)));
  board.width = state.width * CELL;
  board.height = state.height * CELL;
  drawState(state);
}

function drawState(st) {
  if (!st || !ctx) return;
  ctx.clearRect(0, 0, board.width, board.height);
  for(let y=0; y<st.height; y++) {
    for(let x=0; x<st.width; x++) {
      const c = st.cells[y][x];
      const img = assets[c.cell_type];
      if(assetsLoaded && img && img.complete) {
        ctx.drawImage(img, x*CELL, y*CELL, CELL, CELL);
      } else {
        const cols = {0:'#7C8024',1:'#C2B280',2:'#DAA520',3:'#90EE90',4:'#1E90FF',5:'#CD6F26',6:'#000000'};
        ctx.fillStyle = cols[c.cell_type] || '#fff';
        ctx.fillRect(x*CELL, y*CELL, CELL, CELL);
      }
      ctx.strokeStyle='#222'; ctx.strokeRect(x*CELL, y*CELL, CELL, CELL);
      if(c.has_robot) {
        const r = assets['robot'];
        const sz = Math.floor(CELL*0.7);
        const off = (CELL-sz)/2;
        if(assetsLoaded && r && r.complete) ctx.drawImage(r, x*CELL+off, y*CELL+off, sz, sz);
        else {ctx.fillStyle='red'; ctx.fillRect(x*CELL+off, y*CELL+off, sz, sz);}
      }
    }
  }
}

function setupDOM() {
    board = document.getElementById('board');
    if (!board) {
        console.error('Canvas #board not found');
        return;
    }
    ctx = board.getContext('2d');

    board.addEventListener('click', function(e) {
        const r = board.getBoundingClientRect();
        const x = Math.floor((e.clientX - r.left) / CELL);
        const y = Math.floor((e.clientY - r.top) / CELL);
        const url = e.shiftKey ? '/api/place' : '/api/toggle_cell';
        fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({x:x,y:y})}).then(function(){ loadState(); });
    });

    document.getElementById('copy').onclick = function() { document.getElementById('commands').select(); document.execCommand('copy'); };
    document.getElementById('paste').onclick = async function() { const t = await navigator.clipboard.readText(); document.getElementById('commands').value = t; };
    document.getElementById('export').onclick = async function() { const r = await fetch('/api/export'); const j = await r.json(); if(j.code) prompt('Код уровня:', j.code); };
    document.getElementById('import').onclick = async function() { const c = prompt('Вставьте код уровня:'); if(c) { const r = await fetch('/api/import', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({code:c})}); const j = await r.json(); if(j.state) { state = j.state; drawState(state); } } };
    document.getElementById('run').onclick = async function() {
        const raw = document.getElementById('commands').value.split('\\n').map(function(s){ return s.trim(); }).filter(function(s){ return s.length > 0; });
        if(!raw.length) { alert('Нет команд'); return; }
        const r = await fetch('/api/execute', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({commands:raw})});
        const j = await r.json();
        for(const f of j.frames) { drawState(f); await new Promise(function(res){ setTimeout(res,300); }); }
        if(j.victory) {
            alert('Поздравляем! Уровень успешно пройден!');
        } else if(j.message) {
            alert(j.message);
        }
        await loadState();
    };
}

function showMenu(t) {document.getElementById(t+'Modal').style.display = 'block';}
function closeModal(t) {document.getElementById(t).style.display = 'none';}
window.onclick = (e) => {if(e.target.id.includes('Modal')) e.target.style.display = 'none';};

(async () => { setupDOM(); await loadAssets(); await loadState(); })();
</script>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML)

if __name__ == '__main__':
    app.run(debug=True)
