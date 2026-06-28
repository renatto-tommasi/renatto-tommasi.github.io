---
layout: post
title: "When photorealism matters: porting our robot from Gazebo to Isaac Sim for VLM semantic mapping"
date: 2026-06-28 10:00:00+0200
description: A master's thesis on vision-language models for semantic mapping ran into a wall — the simulator's textures weren't realistic enough for models trained on real images. Here's what we learned, and why we ported our robot to Isaac Sim.
tags: robotics simulation perception VLM semantic-mapping ros
categories: research
thumbnail: assets/img/isaac_sim_robot.png
giscus_comments: true
related_posts: false
---

I recently supervised a master's thesis on **vision-language models (VLMs)** and how to fold one into a perception pipeline *without* throwing away the geometry and probabilistic reasoning that semantic mapping is built on. The goal was deliberately conservative: use a VLM to **improve** semantic mapping, not to replace the map with a black box.

We staged the work so the student always had something running:

1. **Baseline.** Build a semantic map driven only by YOLO detections — a known-good, well-understood starting point.
2. **Swap the front end.** Replace YOLO with **SAM 2** for class-agnostic segmentation, so the system proposes object masks instead of fixed-vocabulary boxes.
3. **Add a language head.** Pass each segmented region to a VLM to label it, opening the door to open-vocabulary descriptions the original detector could never produce.

Conceptually, the pipeline worked. The map updated, objects were segmented, and labels came back. But in simulation we hit a wall that turned out to be the most interesting result of the whole thesis.

## The wall: simulators don't look like the real world

SAM 2 and the VLM were trained on **real images**. Our simulation ran in **Gazebo**, and Gazebo's surfaces — flat textures, weak lighting cues, low material fidelity — simply weren't *vivid* enough for SAM 2 to lock onto object boundaries. The segmentation step couldn't reliably crop objects out of the scene, and a language model is only as good as the crop you hand it. Garbage region in, vague label out.

So the bottleneck was never really the model or the pipeline architecture. **It was the simulator.** The domain gap between Gazebo's rendering and the real photographs these models were trained on was wide enough to starve the whole downstream stack of usable input.

{% include figure.liquid loading="eager" path="assets/img/gazebo_environment.png" class="img-fluid rounded z-depth-1" zoomable=true caption="The scene as rendered in Gazebo. Great for physics and navigation — but the flat textures and lighting give models trained on real imagery very little to grab onto." %}

That reframed the question. Instead of asking *"how do we make the VLM smarter?"*, the better question was *"how do we give it input that looks like what it was trained on?"*

## Enter Isaac Sim

[NVIDIA Isaac Sim](https://developer.nvidia.com/isaac/sim) renders with **RTX ray tracing**, which produces scenes that are far closer to real photographs — physically based materials, real reflections, soft shadows, global illumination. If the thesis had run in Isaac Sim from the start, I'm confident the segmentation-plus-VLM stack would have had much more to work with.

So this past weekend I set out to **port the robot to Isaac Sim**. That meant taking the same URDF model we run in Gazebo, bringing it into Isaac Sim, re-mounting every sensor, and wiring up the **ROS topics** so the rest of our stack doesn't know or care which simulator is underneath it. The payoff: the next time a student joins the lab — or when we're prototyping ourselves — and the cameras need to feed a model that expects realistic imagery, we can reach for Isaac Sim instead of Gazebo.

{% include figure.liquid loading="eager" path="assets/img/isaac_sim_robot.png" class="img-fluid rounded z-depth-1" zoomable=true caption="The same robot, now running in Isaac Sim with RTX rendering and the full ROS sensor stack mounted." %}

## So when should you use which?

The lesson here isn't "Isaac Sim is better." It's that **the right simulator depends on what your pipeline consumes.** If your perception is geometric — point clouds, depth, occupancy, fiducials — texture realism barely matters. If your perception is *learned on real images*, photorealism stops being a nice-to-have and becomes the thing that determines whether the pipeline works at all.

### Gazebo

**Pros**
- Lightweight, fast, runs comfortably on modest hardware (no RTX GPU required).
- Mature, deeply integrated ROS/ROS2 tooling and a huge ecosystem of existing models and worlds.
- Excellent for **trajectory planning, navigation, control, and geometry-based object detection**.
- Fast iteration loop — quick to spin up and tweak.

**Cons**
- Rendering is far from photorealistic; textures and lighting are flat.
- Large **sim-to-real gap for vision models trained on real images** (this is exactly what bit us).
- Limited fidelity for camera-heavy perception research.

### Isaac Sim

**Pros**
- **RTX ray-traced, physically based rendering** — lifelike materials, lighting, and reflections.
- Dramatically narrows the domain gap for **models trained on real-world imagery** (SAM 2, VLMs, learned detectors).
- Rich synthetic-data and domain-randomization tooling, plus strong sensor simulation.
- ROS/ROS2 bridge so it slots into an existing stack.

**Cons**
- Heavyweight — needs a capable NVIDIA RTX GPU and more setup effort.
- Steeper learning curve and a smaller community than Gazebo.
- Slower to iterate; more resource-hungry for everyday navigation work.

The short version of what we learned:

> **Gazebo is great for trajectory planning, navigation, and geometry-based detection. But the moment your pipeline depends on models trained on real images, you need a photorealistic renderer — and that's where Isaac Sim earns its cost.**

## What's next

Now that the same robot, sensors, and ROS topics run in **both** simulators, we have a clean way to ask a question we couldn't answer before: **how does the student's segmentation + VLM semantic-mapping pipeline behave in Gazebo versus Isaac Sim, side by side?** Same robot, same sensors, same code — only the renderer changes. In a follow-up I'll run that comparison directly and report how much the photorealistic rendering actually moves the needle on segmentation quality and label accuracy.

If that comparison shows what I expect, it makes a broader point worth internalizing: **as more of our perception stack becomes learned rather than hand-engineered, simulator photorealism stops being cosmetic and becomes a first-class part of the experimental setup.**
