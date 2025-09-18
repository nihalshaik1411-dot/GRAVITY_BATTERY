import streamlit as st
import plotly.graph_objects as go
import time

# Initialize states
if "blocks_A" not in st.session_state:
    st.session_state.blocks_A = 0
    st.session_state.blocks_B = 0
    st.session_state.storage = 0

st.title("⚡ Gravity Battery Animation")

# Add block at A
if st.button("➕ Add Block at A"):
    st.session_state.blocks_A += 1

# Drop from A
if st.button("⬇ Drop from A"):
    if st.session_state.blocks_A > 0:
        st.session_state.blocks_A -= 1
        # Animate drop
        for y in range(10, -10, -1):  # y=10 (top) to y=-10 (underground)
            fig = go.Figure()
            # Ground line
            fig.add_shape(type="line", x0=0, y0=0, x1=10, y1=0, line=dict(color="black", width=3))
            # Falling block
            fig.add_shape(type="rect", x0=4, y0=y, x1=5, y1=y+1,
                          fillcolor="blue", line=dict(color="black"))
            fig.update_yaxes(range=[-12, 12], visible=False)
            fig.update_xaxes(range=[0, 10], visible=False)
            fig.update_layout(height=500, width=700, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig)
            time.sleep(0.1)  # pause for animation

        # After drop → add to storage
        st.session_state.storage += 10

st.subheader("📦 Underground Storage")
st.write(f"Stored Weight: {st.session_state.storage} kg")
