# app.py
import streamlit as st
import time
import plotly.graph_objects as go

st.set_page_config(page_title="Gravity Battery - Continuous Simulation", layout="wide")

# ---------- CONFIG ----------
FRAME_DELAY = 0.08   # seconds per animation frame (lower = faster)
SMALL_DROP_ENERGY = 8  # battery1 units per 10kg drop
BIG_DROP_ENERGY = 80   # battery2 units per 160kg drop
SMALL_DROP_PER_CYCLE = 1  # number of small drops per half-cycle (A then B)
STORAGE_THRESHOLD = 80  # kg to trigger big cycle
# ----------------------------

# ---------- SESSION STATE ----------
if "blocks_A" not in st.session_state:
    st.session_state.blocks_A = 4  # initial 40 kg = 4 blocks
if "blocks_B" not in st.session_state:
    st.session_state.blocks_B = 2  # initial 20 kg = 2 blocks
if "storage_left" not in st.session_state:
    st.session_state.storage_left = 0  # kg stored at C (left)
if "storage_right" not in st.session_state:
    st.session_state.storage_right = 0  # kg stored at D (right)
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
    dropping: None or tuple(point_name e.g. 'A'/'B'/'BIG', color)
    drop_y: y coordinate of top of the falling rectangle
    dropping_size: kg size for annotation (10 or 160)
    """
    fig = go.Figure()
    # Ground line
    fig.add_shape(type="line", x0=-3, y0=0, x1=3, y1=0, line=dict(color="black", width=3))
    # Labels for points (A,B at +50; C,D at -50)
    fig.add_annotation(x=-1.8, y=55, text="A (+50m)", showarrow=False, font=dict(size=12))
    fig.add_annotation(x=1.8, y=55, text="B (+50m)", showarrow=False, font=dict(size=12))
    fig.add_annotation(x=-1.8, y=-55, text="C (−50m)", showarrow=False, font=dict(size=12))
    fig.add_annotation(x=1.8, y=-55, text="D (−50m)", showarrow=False, font=dict(size=12))

    # Draw stacked blocks at A (left) and B (right)
    for i in range(st.session_state.blocks_A):
        y0 = 50 + i * 1.05
        fig.add_shape(type="rect", x0=-2.1, x1=-1.5, y0=y0, y1=y0 + 0.95, fillcolor="#2b6cb0", line=dict(color="black"))
    for i in range(st.session_state.blocks_B):
        y0 = 50 + i * 1.05
        fig.add_shape(type="rect", x0=1.5, x1=2.1, y0=y0, y1=y0 + 0.95, fillcolor="#c53030", line=dict(color="black"))

    # Draw storage at C (left, under A) as stacked orange blocks
    num_left = st.session_state.storage_left // 10
    for i in range(num_left):
        block_top = -50 - i * 1.05
        fig.add_shape(type="rect", x0=-2.1, x1=-1.5, y0=block_top - 0.95, y1=block_top, fillcolor="#dd6b20", line=dict(color="black"))
    
    # Draw storage at D (right, under B) as stacked orange blocks
    num_right = st.session_state.storage_right // 10
    for i in range(num_right):
        block_top = -50 - i * 1.05
        fig.add_shape(type="rect", x0=1.5, x1=2.1, y0=block_top - 0.95, y1=block_top, fillcolor="#dd6b20", line=dict(color="black"))

    # Optional dropping block (animated)
    if dropping and drop_y is not None:
        pt, color = dropping
        if pt == "A":
            x0, x1 = -2.1, -1.5
        elif pt == "B":
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
def animate_fall(placeholder, point_name, color="#2b6cb0", start_y=50, end_y=-50, steps=50, size_kg=10):
    for step in range(steps):
        if st.session_state.stop_requested:
            return False
        t = step / (steps - 1)
        y = start_y + (end_y - start_y) * t
        fig = draw_scene(dropping=(point_name, color), drop_y=y, dropping_size=size_kg)
        placeholder.plotly_chart(fig, use_container_width=True)
        time.sleep(FRAME_DELAY)
    return True

# ---------- MAIN UI ----------
st.title("⚡ Gravity Battery — Continuous Automatic Simulation")

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
    st.session_state.blocks_A = st.number_input("Blocks at A (10kg each)", min_value=0, max_value=50, value=st.session_state.blocks_A, step=1)
    st.session_state.blocks_B = st.number_input("Blocks at B (10kg each)", min_value=0, max_value=50, value=st.session_state.blocks_B, step=1)

with mid_col:
    # placeholder for the animated scene
    scene_ph = st.empty()

with right_col:
    st.subheader("Status")
    total_storage = st.session_state.storage_left + st.session_state.storage_right
    st.write(f"Storage C (left): {st.session_state.storage_left} kg")
    st.write(f"Storage D (right): {st.session_state.storage_right} kg")
    st.write(f"Total Underground storage: {total_storage} kg")
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
    total_storage = st.session_state.storage_left + st.session_state.storage_right

    # SMALL CYCLE PHASE: drop from A to C (if any) - left side
    if st.session_state.blocks_A > 0:
        ok = animate_fall(scene_ph, "A", color="#2b6cb0", start_y=50, end_y=-50, steps=50, size_kg=10)
        if not ok:
            break
        # after drop: block moves to C storage
        st.session_state.storage_left += 10
        st.session_state.blocks_A -= 1  # Remove from A
        st.session_state.generator_angle += 30
        st.session_state.battery1 = min(st.session_state.battery1 + SMALL_DROP_ENERGY, 100)
        # update houses lit state based on battery1 threshold
        st.session_state.houses_lit = st.session_state.battery1 >= 10
        # Log event
        st.session_state.logs.append("Dropped 10kg from A to C storage. Generator rotated +30°. B1 charged +8%.")

    # short pause
    if st.session_state.stop_requested:
        break
    time.sleep(0.2)

    # SMALL CYCLE PHASE: drop from B to D (if any) - right side
    if st.session_state.blocks_B > 0:
        ok = animate_fall(scene_ph, "B", color="#c53030", start_y=50, end_y=-50, steps=50, size_kg=10)
        if not ok:
            break
        st.session_state.storage_right += 10
        st.session_state.blocks_B -= 1  # Remove from B
        st.session_state.generator_angle += 30
        st.session_state.battery1 = min(st.session_state.battery1 + SMALL_DROP_ENERGY, 100)
        st.session_state.houses_lit = st.session_state.battery1 >= 10
        # Log event
        st.session_state.logs.append("Dropped 10kg from B to D storage. Generator rotated +30°. B1 charged +8%.")

    # After both small drops, update UI status snapshot
    scene_ph.plotly_chart(draw_scene(), use_container_width=True)
    time.sleep(0.4)

    # Check for STORAGE threshold -> trigger BIG CYCLE
    total_storage = st.session_state.storage_left + st.session_state.storage_right
    if total_storage >= STORAGE_THRESHOLD:
        # BIG CYCLE: simulate 160kg drop (visual big falling mass)
        # Visual: start at +50 and drop to -50 (bigger shape)
        ok = animate_fall(scene_ph, "BIG", color="#805ad5", start_y=50, end_y=-50, steps=45, size_kg=160)
        if not ok:
            break
        # Big drop charges B2 heavily
        st.session_state.generator_angle += 360
        st.session_state.battery2 = min(st.session_state.battery2 + BIG_DROP_ENERGY, 100)
        # Reset storages (emptied the underground consolidated mass)
        st.session_state.storage_left = 0
        st.session_state.storage_right = 0
        # Use storage energy implicitly; refill A and B with 40kg each (4 blocks each)
        st.session_state.blocks_A += 4
        st.session_state.blocks_B += 4
        # consume some B2 to lift 160kg mass back up (simulate usage)
        st.session_state.battery2 = max(st.session_state.battery2 - 40, 0)
        # update houses / battery1 based on effect
        st.session_state.houses_lit = st.session_state.battery1 >= 10
        # Log event
        st.session_state.logs.append("Storage full (80kg)! Big 160kg drop: Generator full spin. B2 charged +80%. Refilled A & B +40kg each. B2 used -40% for lift.")
        # show immediate scene
        scene_ph.plotly_chart(draw_scene(), use_container_width=True)
        time.sleep(0.6)

    # short break before next cycle iteration
    if st.session_state.stop_requested:
        break
    time.sleep(0.4)

# cleanup: ensure flags are consistent
if st.session_state.stop_requested:
    st.session_state.running = False
    st.session_state.stop_requested = False

# final state render
scene_ph.plotly_chart(draw_scene(), use_container_width=True)

# Event Log display
st.subheader("Event Log")
st.text_area("Simulation Events", value="\n".join(st.session_state.logs), height=200, disabled=True)
