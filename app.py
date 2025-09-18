import streamlit as st
import plotly.graph_objects as go

# --- Initialize session state ---
if "blocks_A" not in st.session_state:
    st.session_state.blocks_A = 0
    st.session_state.blocks_B = 0
    st.session_state.storage = 0
    st.session_state.battery1 = 0
    st.session_state.battery2 = 0
    st.session_state.houses_lit = False

# --- App Title ---
st.title("⚡ Gravity Battery Simulation with Visual Blocks")

# --- Controls for Adding Weights ---
col1, col2 = st.columns(2)
if col1.button("➕ Add 10kg Block at A"):
    st.session_state.blocks_A += 1
if col2.button("➕ Add 10kg Block at B"):
    st.session_state.blocks_B += 1

# --- Drop Simulation ---
def drop_block(point):
    if point == "A" and st.session_state.blocks_A > 0:
        st.session_state.blocks_A -= 1
        process_drop()
    elif point == "B" and st.session_state.blocks_B > 0:
        st.session_state.blocks_B -= 1
        process_drop()

def process_drop():
    st.session_state.battery1 += 5
    st.session_state.storage += 10
    if st.session_state.storage >= 80:
        st.session_state.battery2 += 50
        st.session_state.storage = 0
        st.session_state.houses_lit = True

col3, col4 = st.columns(2)
if col3.button("⬇ Drop from A"):
    drop_block("A")
if col4.button("⬇ Drop from B"):
    drop_block("B")

# --- Visual Representation ---
fig = go.Figure()

# Ground line
fig.add_shape(type="line", x0=0, y0=0, x1=10, y1=0, line=dict(color="black", width=3))

# Blocks at A
for i in range(st.session_state.blocks_A):
    fig.add_shape(type="rect", x0=1, y0=i*1.2+1, x1=2, y1=i*1.2+2,
                  fillcolor="blue", line=dict(color="black"))

# Blocks at B
for i in range(st.session_state.blocks_B):
    fig.add_shape(type="rect", x0=8, y0=i*1.2+1, x1=9, y1=i*1.2+2,
                  fillcolor="green", line=dict(color="black"))

# Underground storage (C & D)
for i in range(st.session_state.storage // 10):
    fig.add_shape(type="rect", x0=4, y0=-i*1.2-1, x1=5, y1=-i*1.2,
                  fillcolor="orange", line=dict(color="black"))

# Batteries
fig.add_annotation(x=0.5, y=6, text=f"🔋 B1: {st.session_state.battery1}", showarrow=False)
fig.add_annotation(x=9.5, y=6, text=f"🔋 B2: {st.session_state.battery2}", showarrow=False)

fig.update_yaxes(range=[-12, 12], visible=False)
fig.update_xaxes(range=[0, 10], visible=False)
fig.update_layout(height=500, width=700, showlegend=False, margin=dict(l=20, r=20, t=20, b=20))

st.plotly_chart(fig)

# --- Houses Lighting Status ---
if st.session_state.houses_lit:
    st.success("🏠 Houses are lit using Battery B2!")
else:
    st.warning("Houses are waiting for Battery B2 power...")
