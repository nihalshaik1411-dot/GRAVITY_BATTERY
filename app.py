```python
# app.py
import streamlit as st
import time
import plotly.graph_objects as go

st.set_page_config(page_title="Gravity Battery - Alternative Seesaw Simulation", layout="wide")

# ---------- CONFIG ----------
FRAME_DELAY = 0.08   # seconds per animation frame (lower = faster)
SMALL_DROP_ENERGY = 8  # battery1 units per 10kg drop
BIG_DROP_ENERGY = 80   # battery2 units per 160kg drop
STORAGE_THRESHOLD = 80  # kg to trigger big cycle
# ----------------------------

# ---------- SESSION STATE ----------
if "blocks_top_A" not in st.session_state:
    st.session_state.blocks_top_A = 1  # initial 10 kg = 1 block
if "blocks_top_B" not in st.session_state:
    st.session_state.blocks_top_B = 2  # initial 20 kg = 2 blocks
if "tied_bottom_C" not in st.session_state:
    st.session_state.tied_bottom_C = 0  # tied blocks at C
if "tied_bottom_D" not in st.session_state:
    st.session_state.tied_bottom_D = 0  # tied blocks at D
if "storage_left" not in st.session_state:
    st.session_state.storage_left = 0  # kg stored at left (C)
if "storage_right" not in st.session_state:
    st.session_state.storage_right = 0  # kg stored at right (D)
if "battery1" not in st.session_state:
    st.session_state.battery1 = 0  # small battery % (0-100)
if "battery2" not in st.session_state:
    st.session_state.battery2 = 0  # big battery % (0-100)
if "generator_angle" not in st.session_state:
    st.session_state.generator_angle = 0
if "houses_lit" not in st.session_state:
    st.session_state.houses_lit = False
if "running" not in st.session_state:
    st.session_state.running = False
if "logs" not in st.session_state:
    st.session_state.logs = []
# For animation control (to gracefully stop loops)
if "stop_requested" not in st.session_state:
    st.session_state.stop_requested = False
# ----------------------------

# ---------- DRAW / ANIMATION HELPERS ----------
def draw_scene(dropping=None, drop_y=None, dropping_size=10, note=""):
    """
    dropping: None or tuple(point_name e.g. 'left'/'right'/'BIG', color)
    drop_y: y coordinate of top of the falling rectangle
    dropping_size: kg size for annotation (20 or 160)
    """
    fig = go.Figure()
    # Ground line
    fig.add_shape(type="line", x0=-3, y0=0, x1=3, y1=0, line=dict(color="black", width=3))
    # Labels for points (A,B at +50; C,D at -50)
    fig.add_annotation(x=-1.8, y=55, text="A (+50m)", showarrow=False, font=dict(size=12))
    fig.add_annotation(x=1.8, y=55, text="B (+50m)", showarrow=False, font=dict(size=12))
    fig.add_annotation(x=-1.8, y=-55, text="C (−50m)", showarrow=False, font=dict(size=12))
    fig.add_annotation(x=1.8, y=-55, text="D (−50m)", showarrow=False, font=dict(size=12))

    # Draw stacked blocks at top A (left, blue)
    for i in range(st.session_state.blocks_top_A):
        y0 = 50 + i * 1.05
        fig.add_shape(type="rect", x0=-2.1, x1=-1.5, y0=y0, y1=y0 + 0.95, fillcolor="#2b6cb0", line=dict(color="black"))
    # Draw stacked blocks at top B (right, red)
    for i in range(st.session_state.blocks_top_B):
        y0 = 50 + i * 1.05
        fig.add_shape(type="rect", x0=1.5, x1=2.1, y0=y0, y1=y0 + 0.95, fillcolor="#c53030", line=dict(color="black"))

    # Tied block at bottom C (left, gray if present)
    if st.session_state.tied_bottom_C > 0:
        fig.add_shape(type="rect", x0=-2.1, x1=-1.5, y0=-51, y1=-50.05, fillcolor="gray", line=dict(color="black"))
    # Tied block at bottom D (right, gray if present)
    if st.session_state.tied_bottom_D > 0:
        fig.add_shape(type="rect", x0=1.5, x1=2.1, y0=-51, y1=-50.05, fillcolor="gray", line=dict(color="black"))

    # Stored blocks at left (below tied, orange)
    num_stored_left = st.session_state.storage_left // 10
    base_y_left = -51.05
    for i in range(num_stored_left):
        y1 = base_y_left - i * 1.05
        y0 = y1 - 0.95
        fig.add_shape(type="rect", x0=-2.1, x1=-1.5, y0=y0, y1=y1, fillcolor="#dd6b20", line=dict(color="black"))
    # Stored blocks at right (below tied, orange)
    num_stored_right = st.session_state.storage_right // 10
    base_y_right = -51.05
    for i in range(num_stored_right):
        y1 = base_y_right - i * 1.05
        y0 = y1 - 0.95
        fig.add_shape(type="rect", x0=1.5, x1=2.1, y0=y0, y1=y1, fillcolor="#dd6b20", line=dict(color="black"))

    # Optional dropping block (animated)
    if dropping and drop_y is not None:
        pt, color = dropping
        if pt == "left":
            x0, x1 = -2.1, -1.5
        elif pt == "right":
            x0, x1 = 1.5, 2.1
        elif pt == "BIG":
            # big drop centered (wider)
            x0, x1 = -1.2, 1.2
        else:
            x0, x1 = -0.6, 0.6
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=drop_y, y1=drop_y + 0.95, fillcolor=color, line=dict(color="black"))
        fig.add_annotation(x=0, y=drop_y + 1.2, text=f"Dropping: {dropping_size}kg", showarrow=False)

    # Generator visual (circle) and angle
    angle = st.session_state.generator_angle % 360
    fig.add_shape(type="circle", x0=-0.4, y0=-20.6, x1=0.4, y1=-21.6, line=dict(color="orange", width=3))
    fig.add_annotation(x=0, y=-21.1, text=f"⚙ {angle:.0f}°", showarrow=False, font=dict(color="orange"))

    # Battery labels (top left/right)
    fig.add_annotation(x=-2.7, y=45, text=f"🔋 B1: {st.session_state.battery1:.0f}%", showarrow=False)
    fig.add_annotation(x=2.7, y=45, text=f"🔋 B2: {st.session_state.battery2:.0f}%", showarrow=False)

    # Houses indicator (top center)
    houses_text = "🏠 lit" if st.session_state.houses_lit else "🏠 dark"
    fig.add_annotation(x=0, y=45, text=houses_text, showarrow=False)

    fig.update_xaxes(visible=False, range=[-4, 4])
    fig.update_yaxes(visible=False, range=[-65, 65])
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=10, b=10))
    return fig

# Helper to animate a falling rectangle from start_y to end_y with steps
def animate_fall(placeholder, pt, color="#2b6cb0", start_y=50, end_y=-50, steps=50, size_kg=20):
    for step in range(steps):
        if st.session_state.stop_requested:
            return False
        t = step / (steps - 1)
        y = start_y + (end_y - start_y) * t
        fig = draw_scene(dropping=(pt, color), drop_y=y, dropping_size=size_kg)
        placeholder.plotly_chart(fig, use_container_width=True)
        time.sleep(FRAME_DELAY)
    return True

# ---------- MAIN UI ----------
st.title("⚡ Gravity Battery — Alternative Seesaw Continuous Simulation")

left_col, mid_col, right_col = st.columns([1, 2, 1])

with left_col:
    st.subheader("Controls")
    if st.button("Start"):
        st.session_state.running = True
        st.session_state.stop_requested = False
        st.session_state.logs = []  # Clear logs on start
    if st.button("Stop"):
        st.session_state.stop_requested = True
        st.session_state.running = False

    st.write("Initial top stacks (editable):")
    st.session_state.blocks_top_A = st.number_input("Blocks at top A (10kg each)", min_value=0, max_value=50, value=st.session_state.blocks_top_A, step=1)
    st.session_state.blocks_top_B = st.number_input("Blocks at top B (10kg each)", min_value=0, max_value=50, value=st.session_state.blocks_top_B, step=1)

with mid_col:
    # placeholder for the animated scene
    scene_ph = st.empty()

with right_col:
    st.subheader("Status")
    total_storage = st.session_state.storage_left + st.session_state.storage_right
    st.write(f"Top A: {st.session_state.blocks_top_A * 10} kg")
    st.write(f"Top B: {st.session_state.blocks_top_B * 10} kg")
    st.write(f"Tied at C: {st.session_state.tied_bottom_C * 10} kg")
    st.write(f"Tied at D: {st.session_state.tied_bottom_D * 10} kg")
    st.write(f"Storage left (C): {st.session_state.storage_left} kg")
    st.write(f"Storage right (D): {st.session_state.storage_right} kg")
    st.write(f"Total storage: {total_storage} kg")
    st.write(f"Battery B1: {st.session_state.battery1:.0f}%")
    st.write(f"Battery B2: {st.session_state.battery2:.0f}%")
    st.write(f"Generator angle: {st.session_state.generator_angle:.0f}°")
    if st.session_state.houses_lit:
        st.success("Houses are lit by B1!")
    else:
        st.info("Houses are not lit yet")

# initial scene draw if not running
if not st.session_state.running:
    scene_ph.plotly_chart(draw_scene(), use_container_width=True)

# ---------- AUTOMATIC LOOP ----------
# The loop runs while running == True. It will exit cleanly when Stop is pressed.
while st.session_state.running and not st.session_state.stop_requested:
    dropped = False
    side = None
    opposite = None
    color = None
    lifted = 0

    # Check for left drop
    if st.session_state.blocks_top_A == 2 and st.session_state.blocks_top_B < 2:
        ok = animate_fall(scene_ph, "left", color="#2b6cb0", steps=50, size_kg=20)
        if not ok:
            break
        st.session_state.blocks_top_A = 0
        st.session_state.storage_left += 10
        st.session_state.tied_bottom_C += 1
        # Lift right
        lifted = st.session_state.tied_bottom_D
        st.session_state.blocks_top_B += lifted
        st.session_state.tied_bottom_D = 0
        side = "left"
        opposite = "right"
        color = "#2b6cb0"
        dropped = True
    # Check for right drop
    elif st.session_state.blocks_top_B == 2 and st.session_state.blocks_top_A < 2:
        ok = animate_fall(scene_ph, "right", color="#c53030", steps=50, size_kg=20)
        if not ok:
            break
        st.session_state.blocks_top_B = 0
        st.session_state.storage_right += 10
        st.session_state.tied_bottom_D += 1
        # Lift left
        lifted = st.session_state.tied_bottom_C
        st.session_state.blocks_top_A += lifted
        st.session_state.tied_bottom_C = 0
        side = "right"
        opposite = "left"
        color = "#c53030"
        dropped = True

    if not dropped:
        time.sleep(0.2)
        continue

    # Generate power for small drop (20kg)
    st.session_state.battery1 = min(st.session_state.battery1 + SMALL_DROP_ENERGY * 2, 100)
    st.session_state.generator_angle += 30 * 2  # 60° for 20kg
    st.session_state.houses_lit = st.session_state.battery1 >= 10

    # Log drop event
    lift_to = "B" if opposite == "right" else "A"
    drop_to = "C" if side == "left" else "D"
    st.session_state.logs.append(f"Dropped 20kg from {side.upper()} to {drop_to}, stored 10kg, tied 10kg. Lifted {lifted * 10}kg to {lift_to}. B1 +16%, Generator +60°.")

    # Add 10kg to opposite side
    if opposite == "left":
        st.session_state.blocks_top_A += 1
        add_side = "A"
    else:
        st.session_state.blocks_top_B += 1
        add_side = "B"
    st.session_state.logs.append(f"Added 10kg to {add_side}.")

    # Update scene
    scene_ph.plotly_chart(draw_scene(), use_container_width=True)
    time.sleep(0.4)

    # Check for STORAGE threshold -> trigger BIG CYCLE
    total_storage = st.session_state.storage_left + st.session_state.storage_right
    if total_storage >= STORAGE_THRESHOLD:
        # BIG CYCLE: simulate 160kg drop (visual big falling mass)
        ok = animate_fall(scene_ph, "BIG", color="#805ad5", steps=60, size_kg=160)
        if not ok:
            break
        # Big drop charges B2 heavily
        st.session_state.generator_angle += 360
        st.session_state.battery2 = min(st.session_state.battery2 + BIG_DROP_ENERGY, 100)
        # Reset storages
        st.session_state.storage_left = 0
        st.session_state.storage_right = 0
        # Use B2 energy to lift 160kg back up
        st.session_state.battery2 = max(st.session_state.battery2 - 40, 0)
        # Log event
        st.session_state.logs.append("Big cycle: Dropped 160kg, B2 +80%, full spin. Reset storages. Used 40% B2 to lift 160kg up.")
        # update houses
        st.session_state.houses_lit = st.session_state.battery1 >= 10
        # show immediate scene
        scene_ph.plotly_chart(draw_scene(), use_container_width=True)
        time.sleep(0.6)

    if st.session_state.stop_requested:
        break
    time.sleep(0.2)

# cleanup: ensure flags are consistent
if st.session_state.stop_requested:
    st.session_state.running = False
    st.session_state.stop_requested = False

# final state render
scene_ph.plotly_chart(draw_scene(), use_container_width=True)

# Event Log display
st.subheader("Event Log")
st.text_area("Simulation Events", value="\n".join(st.session_state.logs), height=200, disabled=True)
```

---

### Key Upgrades for Alternative Seesaw Run
- **Seesaw Mechanics**: Implemented coupled drops via pulley/generator connection. Starts with 10kg at A (stable), 20kg at B. Drops 20kg from heavier side (initially B to D), stores 10kg at D, ties 10kg at D for future lift. Adds 10kg to A (now 20kg). Next drop from A to C pulls tied 10kg from D up to B, stores 10kg at C, ties 10kg at C. Adds 10kg to B (now 20kg). Alternates continuously, generating power to B1 per 20kg drop (+16%).
- **Visualization**: Tied blocks (gray) at bottom positions (-50m). Stored blocks (orange) stacked below tied. Drops animated as 20kg (labeled, same width for simplicity).
- **Storage & Big Cycle**: +10kg stored per drop (alternating sides). At 80kg total, drops 160kg central (purple, wider), charges B2 +80%, resets storages to 0, consumes 40% B2 to lift 160kg back. Small cycle continues independently (adds simulate ongoing input).
- **Logs**: Detailed events for drops, lifts, adds, and big cycle.
- **Initial Setup**: Top A=1 block (10kg), B=2 (20kg). Editables in controls.
- **Energy**: B1 charges +16% per small drop (20kg), powers houses ≥10%. Generator rotates +60° per small, +360° big.

Run as before (locally or Streamlit Cloud). If you want tweaks (e.g., wider drops for 20kg, variable add amounts, or tied visuals adjusted), let me know!
