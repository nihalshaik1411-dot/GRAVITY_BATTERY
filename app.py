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
# ----------------------------

# ---------- SESSION STATE ----------
if "blocks_A" not in st.session_state:
    st.session_state.blocks_A = 4  # initial 40 kg = 4 blocks
if "blocks_B" not in st.session_state:
    st.session_state.blocks_B = 2  # initial 20 kg = 2 blocks
if "storage" not in st.session_state:
    st.session_state.storage = 0  # kg stored underground
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

    # Draw storage (center underground) as stacked green blocks
    stored_blocks = st.session_state.storage // 10
    for i in range(stored_blocks):
        y0 = -1 - i * 1.05
        fig.add_shape(type="rect", x0=-0.6, x1=0.6, y0=y0 - 0.95, y1=y0, fillcolor="#dd6b20", line=dict(color="black"))

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
def animate_fall(placeholder, point_name, color="#2b6cb0", start_y=50, end_y=-50, steps=40, size_kg=10):
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
    st.write(f"Underground storage: {st.session_state.storage} kg")
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
    # SMALL CYCLE PHASE: drop from A (if any)
    if st.session_state.blocks_A > 0:
        ok = animate_fall(scene_ph, "A", color="#2b6cb0", start_y=50, end_y=-10, steps=30, size_kg=10)
        if not ok:
            break
        # after drop: block moves to lower storage area (we simulate transit)
        st.session_state.storage += 10
        st.session_state.generator_angle += 30
        st.session_state.battery1 = min(st.session_state.battery1 + SMALL_DROP_ENERGY, 100)
        # update houses lit state based on battery1 threshold
        st.session_state.houses_lit = st.session_state.battery1 >= 10

    # short pause
    if st.session_state.stop_requested:
        break
    time.sleep(0.2)

    # SMALL CYCLE PHASE: drop from B (if any)
    if st.session_state.blocks_B > 0:
        ok = animate_fall(scene_ph, "B", color="#c53030", start_y=50, end_y=-10, steps=30, size_kg=10)
        if not ok:
            break
        st.session_state.storage += 10
        st.session_state.generator_angle += 30
        st.session_state.battery1 = min(st.session_state.battery1 + SMALL_DROP_ENERGY, 100)
        st.session_state.houses_lit = st.session_state.battery1 >= 10

    # After both A and B small drops, update UI status snapshot
    scene_ph.plotly_chart(draw_scene(), use_container_width=True)
    time.sleep(0.4)

    # Check for STORAGE threshold -> trigger BIG CYCLE
    if st.session_state.storage >= 80:
        # BIG CYCLE: simulate 160kg drop (visual big falling mass)
        # Visual: start at +50 and drop to -50 (bigger shape)
        ok = animate_fall(scene_ph, "BIG", color="#805ad5", start_y=50, end_y=-50, steps=45, size_kg=160)
        if not ok:
            break
        # Big drop charges B2 heavily
        st.session_state.generator_angle += 360
        st.session_state.battery2 = min(st.session_state.battery2 + BIG_DROP_ENERGY, 100)
        # Reset storage (we emptied the underground consolidated mass)
        st.session_state.storage = 0
        # Use Battery B2 energy to refill A and B with 40kg each (4 blocks each)
        st.session_state.blocks_A += 4
        st.session_state.blocks_B += 4
        # consume some B2 to lift mass back up (simulate usage)
        st.session_state.battery2 = max(st.session_state.battery2 - 40, 0)
        # update houses / battery1 based on effect
        st.session_state.houses_lit = st.session_state.battery1 >= 10
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
