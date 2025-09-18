import streamlit as st
import time
import plotly.graph_objects as go

st.set_page_config(page_title="Gravity Battery Simulator", layout="wide")

# --- Session State ---
if "blocks_A" not in st.session_state:
    st.session_state.blocks_A = 4   # 4 blocks (40kg) at A
if "blocks_B" not in st.session_state:
    st.session_state.blocks_B = 2   # 2 blocks (20kg) at B
if "storage" not in st.session_state:
    st.session_state.storage = 0    # underground storage
if "battery1" not in st.session_state:
    st.session_state.battery1 = 0   # charge level
if "generator_angle" not in st.session_state:
    st.session_state.generator_angle = 0
if "houses_lit" not in st.session_state:
    st.session_state.houses_lit = False


# --- Functions ---
def drop_block(from_point, placeholder):
    if from_point == "A" and st.session_state.blocks_A > 0:
        st.session_state.blocks_A -= 1
        animate_drop("A", placeholder)
    elif from_point == "B" and st.session_state.blocks_B > 0:
        st.session_state.blocks_B -= 1
        animate_drop("B", placeholder)
    else:
        st.warning("No blocks available to drop!")


def animate_drop(point, placeholder):
    """Simulates block dropping and generator rotation"""
    for y in range(50, -51, -10):  # from +50m to -50m
        fig = draw_scene(drop_point=point, drop_y=y)
        placeholder.plotly_chart(fig, use_container_width=True)
        time.sleep(0.2)

    # after drop → block goes to storage
    st.session_state.storage += 10
    st.session_state.generator_angle += 45
    st.session_state.battery1 += 10
    if st.session_state.battery1 >= 20:
        st.session_state.houses_lit = True


def draw_scene(drop_point=None, drop_y=None):
    """Draws A,B above ground and C,D underground with optional drop"""
    fig = go.Figure()

    # Ground line
    fig.add_shape(type="line", x0=-2, y0=0, x1=2, y1=0, line=dict(color="black", width=3))

    # Points labels
    fig.add_annotation(x=-1, y=55, text="A", showarrow=False)
    fig.add_annotation(x=1, y=55, text="B", showarrow=False)
    fig.add_annotation(x=-1, y=-55, text="C", showarrow=False)
    fig.add_annotation(x=1, y=-55, text="D", showarrow=False)

    # Draw static blocks at A and B
    for i in range(st.session_state.blocks_A):
        fig.add_shape(type="rect", x0=-1.2, x1=-0.8, y0=50+i, y1=51+i, fillcolor="blue")
    for i in range(st.session_state.blocks_B):
        fig.add_shape(type="rect", x0=0.8, x1=1.2, y0=50+i, y1=51+i, fillcolor="red")

    # Storage blocks
    for i in range(st.session_state.storage // 10):
        fig.add_shape(type="rect", x0=-0.2, x1=0.2, y0=-i-1, y1=-i, fillcolor="green")

    # Dropping block
    if drop_point and drop_y is not None:
        color = "blue" if drop_point == "A" else "red"
        fig.add_shape(type="rect", x0=-1.2 if drop_point=="A" else 0.8,
                                   x1=-0.8 if drop_point=="A" else 1.2,
                                   y0=drop_y, y1=drop_y+1, fillcolor=color)

    # Generator (circle with rotation angle)
    angle = st.session_state.generator_angle % 360
    fig.add_shape(type="circle", x0=-0.5, y0=-20, x1=0.5, y1=-21, line=dict(color="orange", width=3))
    fig.add_annotation(x=0, y=-20.5, text=f"⚙ {angle}°", showarrow=False, font=dict(color="orange"))

    # Layout
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, range=[-60, 60])
    fig.update_layout(height=500, margin=dict(l=20, r=20, t=20, b=20))
    return fig


# --- UI ---
st.title("⚡ Gravity Battery Simulator (Prototype)")

col1, col2, col3 = st.columns(3)

# Create placeholder here once
placeholder = st.empty()

with col1:
    st.subheader("Controls")
    if st.button("Drop from A (10kg)"):
        drop_block("A", placeholder)
    if st.button("Drop from B (10kg)"):
        drop_block("B", placeholder)

with col2:
    st.subheader("Battery B1")
    st.progress(min(st.session_state.battery1, 100) / 100)

with col3:
    st.subheader("Houses")
    if st.session_state.houses_lit:
        st.success("🏠 Houses Lit!")
    else:
        st.info("🏠 Dark")

# Draw main scene
fig = draw_scene()
placeholder.plotly_chart(fig, use_container_width=True)
