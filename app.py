import streamlit as st
import time

# App Title
st.title("⚡ Gravity Battery Simulation")

# States
if "blocks_A" not in st.session_state:
    st.session_state.blocks_A = 0
    st.session_state.blocks_B = 0
    st.session_state.storage = 0
    st.session_state.battery1 = 0
    st.session_state.battery2 = 0
    st.session_state.houses_lit = False

# Controls
col1, col2 = st.columns(2)
if col1.button("➕ Add 10kg Block at A"):
    st.session_state.blocks_A += 1
if col2.button("➕ Add 10kg Block at B"):
    st.session_state.blocks_B += 1

st.write(f"Blocks at A: {st.session_state.blocks_A} | B: {st.session_state.blocks_B}")

# Drop simulation
def drop_block(point):
    if point == "A" and st.session_state.blocks_A > 0:
        st.session_state.blocks_A -= 1
        process_drop()
    elif point == "B" and st.session_state.blocks_B > 0:
        st.session_state.blocks_B -= 1
        process_drop()

def process_drop():
    st.session_state.battery1 += 5  # Generator small charge
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

# Status
st.subheader("📦 Storage & ⚡ Energy")
st.write(f"Underground Storage: {st.session_state.storage} kg")
st.write(f"Battery B1: {st.session_state.battery1} units")
st.write(f"Battery B2: {st.session_state.battery2} units")

if st.session_state.houses_lit:
    st.success("🏠 Houses are lit! Using Battery B2 power.")
else:
    st.warning("Houses are waiting for power...")
