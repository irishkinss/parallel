import tkinter as tk
from tkinter import ttk
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def create_gui(root):
    # Frame for parameters
    param_frame = ttk.LabelFrame(root, text="Simulation Parameters", padding="10")
    param_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")

    # Input fields for parameters
    num_particles_label = ttk.Label(param_frame, text="Number of Particles:")
    num_particles_entry = ttk.Entry(param_frame)
    num_particles_entry.insert(0, '30')
    
    cube_size_label = ttk.Label(param_frame, text="Cube Size:")
    cube_size_entry = ttk.Entry(param_frame)
    cube_size_entry.insert(0, '5.0')
    
    dt_label = ttk.Label(param_frame, text="Time Step (dt):")
    dt_entry = ttk.Entry(param_frame)
    dt_entry.insert(0, '0.05')

    # Buttons to start and stop
    start_button = ttk.Button(param_frame, text="Start", command=lambda: None)  # Replace with actual start method
    stop_button = ttk.Button(param_frame, text="Stop", command=lambda: None)    # Replace with actual stop method

    # Layout
    num_particles_label.grid(row=0, column=0, sticky="w")
    num_particles_entry.grid(row=0, column=1)
    
    cube_size_label.grid(row=1, column=0, sticky="w")
    cube_size_entry.grid(row=1, column=1)
    
    dt_label.grid(row=2, column=0, sticky="w")
    dt_entry.grid(row=2, column=1)

    start_button.grid(row=3, column=0, pady=10)
    stop_button.grid(row=3, column=1)

    # Frame for canvas (this frame will contain the plot)
    canvas_frame = ttk.Frame(root)
    canvas_frame.grid(row=0, column=0, padx=10, pady=10)

    # Setup Matplotlib figure for visualization
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlim(-2.5, 2.5)
    ax.set_ylim(-2.5, 2.5)
    ax.set_zlim(-2.5, 2.5)
    scatter = ax.scatter([], [], [], s=10)

    # Create the canvas after setting up the frame
    canvas = fig.canvas.get_tk_widget()
    canvas.pack(in_=canvas_frame, expand=True, fill=tk.BOTH)  # Using .pack() here instead of .grid()

    # Start animation
    animation = FuncAnimation(fig, lambda frame: None, interval=100, blit=False)
    fig.canvas.draw()

    return {
        'param_frame': param_frame,
        'canvas_frame': canvas_frame,
        'fig': fig,
        'ax': ax,
        'canvas': canvas,
        'start_button': start_button,
        'stop_button': stop_button
    }

