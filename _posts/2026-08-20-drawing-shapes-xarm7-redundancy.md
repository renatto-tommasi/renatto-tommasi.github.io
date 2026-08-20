---
layout: post
title: "The 7th joint is a decision, not a bonus: drawing shapes in the air with an xArm 7"
date: 2026-08-20 09:00:00+0200
description: A robotics challenge asked me to trace 2D shapes in 3D space with a 7-DoF arm. The interesting part wasn't the geometry — it was that a redundant arm gives you infinitely many ways to hold the pen, and picking greedily gets you stuck two thirds of the way around the outline.
tags: robotics motion-planning moveit kinematics manipulation ros
categories: projects
thumbnail: assets/img/avatar_challenge_rviz.png
giscus_comments: true
related_posts: false
---

I recently worked through a robotics challenge with a deceptively simple brief: **read a set of 2D shapes from a file and trace them in the air with a simulated 7-DoF arm**, holding the tool normal to each shape's plane. A square, a triangle, a stadium made of arcs, a closed B-spline — draw them, on planes placed anywhere in the workspace, at any orientation.

The geometry is a warm-up. The part that turned out to be genuinely interesting is the part the brief doesn't mention: a **UFactory xArm 7** has seven joints, and drawing with a pen only needs six. That extra degree of freedom isn't free capability you get to ignore. It's a choice you are making whether or not you notice you're making it — and the default way of making it is quietly wrong.

The code is on GitHub: [renatto-tommasi/avatar_challenge](https://github.com/renatto-tommasi/avatar_challenge).

{% include figure.liquid loading="eager" path="assets/img/avatar_challenge_rviz.png" class="img-fluid rounded z-depth-1" zoomable=true caption="The four demo shapes traced. Green is the commanded outline, magenta is the tool path actually swept during execution — reconstructed by forward kinematics over the executed trajectory. The translucent blue patches are each shape's plane, and the small RGB triads are the shape frames. The arm has parked at home so the drawings are unobstructed." %}

## First, make the hard requirement disappear

Before any of the redundancy work, there's a modelling decision that pays for itself repeatedly: **every shape is authored in 2D, inside its own frame.**

Each shape gets a frame `S` where the origin is the shape's first vertex — the brief fixes it at `(0, 0)`, so it's a validated invariant rather than a convention — and where **the XY plane of `S` is the drawing plane**. That means the plane normal isn't something you compute. It's just `Z_S`.

A single rigid transform lifts every authored coordinate into robot coordinates:

```
p_base = T_base_shape · (x, y, standoff)
```

And now both hard requirements fall out for free.

**"Tool normal to the plane"** stops being a per-waypoint constraint you have to enforce and re-check. It becomes "the tool's approach axis is parallel to `Z_S`" — a property of the _frame_, not of any individual point on the outline. So the tool orientation is computed **once per shape** and shared by every waypoint:

```
R_base_tool = R_base_S · Rx(π) · Rz(spin)
```

The `Rx(π)` flips the end-effector's `+Z` to point along `−Z_S` — "into the page", like holding a pen.

**"Rotate the shape 45° about Z"** — a requirement that sounds like it needs its own code path — is literally `orientation_rpy: [0, 0, 45]` in the YAML. Because the geometry never leaves 2D, rotating the frame rotates the shape _and_ the tool together, with no extra work anywhere.

Each shape frame is also published on TF as `shape_<name>`, so the whole mapping is directly inspectable in RViz instead of being an article of faith.

## The actual problem: which arm draws the shape?

Here's the thing about a 7-DoF arm doing a 6-DoF task. The inverse kinematics doesn't have _a_ solution. It has a **one-parameter family** of them — the _self-motion manifold_. Every point on that manifold puts the tool in exactly the same place, with the elbow swung somewhere else entirely.

Which point you pick determines three things that matter:

- whether the **whole shape** stays inside the joint limits,
- how far the arm has to travel to get into position from wherever it currently is,
- and how close it drifts to a **singularity** halfway through the trace.

The obvious implementation — solve IK at the first waypoint, start drawing — throws all three away. It takes whatever the numeric solver happens to converge to from the current seed. That's not a decision; that's an accident.

So instead, `RedundancyResolver` does this:

1. **Land on the manifold once**, seeding IK from the robot's _current_ joint state (random restarts only as a fallback).
2. **Walk along it in both directions.** The Jacobian `J` is 6×7, so its null space is spanned by the last right-singular vector of its SVD. Stepping along that vector leaves the tool pose unchanged _to first order_; re-solving IK for the same entry pose cancels the second-order drift. Repeat, and you get a set of genuinely distinct postures for one identical tool pose.
3. **Dry-run the entire shape from each candidate** — IK-chaining waypoint to waypoint exactly the way MoveIt's Cartesian interpolator will. A configuration that dies two thirds of the way round gets caught _before anything moves_.
4. **Score and rank them.**

| term       | what it measures                                                |
| ---------- | --------------------------------------------------------------- |
| `approach` | weighted joint distance from the current configuration          |
| `path`     | weighted joint travel accumulated while drawing                 |
| `limits`   | worst normalised joint-limit proximity along the trace          |
| `manip`    | reciprocal of the worst manipulability `√det(JJᵀ)` on the trace |

Joints are weighted individually — the default is `[2.0, 1.8, 1.4, 1.2, 0.8, 0.6, 0.4]` — because swinging joint 1 drags the entire arm across the workspace, while spinning joint 7 barely moves anything. Treating them as equal-cost misprices every comparison.

The winner is commanded as a **joint-space goal, not a pose goal**, so the arm arrives in the posture that was actually evaluated rather than whatever IK reinvents at execution time. Only then does the Cartesian trace run.

## The evidence that greedy IK is wrong

The ranking is printed for every shape, which makes the effect concrete. Here's the stadium from the demo run — a shape that _is_ reachable, but only from part of its manifold:

```
Shape 'stadium': evaluated 11 configuration(s) on the self-motion manifold
      rank  psi[rad]  spin  reach  approach   path  limits  manip  min|J|   total
         0    -1.400  0.000  1.000     3.852  2.338   0.443  1.359   0.037  10.551
         1    -1.200  0.000  1.000     3.705  2.438   0.418  1.512   0.033  10.719
         2    -1.000  0.000  1.000     3.557  2.640   0.395  1.809   0.028  11.239
         3    -0.800  0.000  0.593     3.409  1.551   0.374  1.901   0.026  1416.379  (incomplete)
         4    -0.600  0.000  0.444     3.264  1.258   0.356  1.981   0.025  1563.850  (incomplete)
         5    -0.400  0.000  0.407     3.122  1.205   0.344  2.307   0.022  1600.947  (incomplete)
         6    -1.600  0.000  0.222     3.999  0.714   0.435  1.122   0.045  1784.979  (incomplete)
         7    -1.800  0.000  0.111     4.145  0.553   0.440  1.041   0.048  1895.842  (incomplete)
```

**Only three of eleven candidates can trace the whole outline.**

Now look at ranks 3–5. They are all _closer_ to the arm's current configuration than the winner — `approach` of 3.1–3.4 against the winner's 3.85 — and they have a _lower_ drawing cost. Every local signal says they're better. A greedy IK seed would pick one happily.

And they stall between **40% and 60%** of the way around the shape.

That's the whole argument in one table. The information that distinguishes a good posture from a doomed one **does not exist at the first waypoint**. You can only get it by simulating the rest of the trace, and by then the greedy solver has already committed. This is why the dry-run step is the expensive part of the search and also the only part that actually matters.

Every candidate configuration, and every waypoint of its dry run, is also checked against a `planning_scene::PlanningScene` built from the robot model — so it carries the SRDF's allowed-collision matrix, and a posture that folds the arm into itself is discarded during the search rather than rejected later by the Cartesian planner.

### The second free parameter nobody uses

There's more slack in this task than the 7th joint. Tracing a shape with a pen really only constrains **5 DoF** — the rotation of the tool _about_ the plane normal is task-irrelevant. Nothing about the drawing changes if you spin the pen in your fingers.

Setting `tool.free_spin: true` treats that angle as a second search dimension: the manifold is re-enumerated at each of `spin_samples` angles, and the best configuration across all of them wins. One spin angle is then held constant for the whole shape, so the tool still stays rigidly normal to the plane.

On a square 400 mm out on a vertical plane, enabling it evaluates **112 configurations instead of 21**, and settles on a tool roll of 2.09 rad rather than the authored 0. It's off by default so runs stay deterministic and match the authored tool pose — but it's a good illustration that "how many degrees of freedom does this task leave me" is worth asking explicitly.

## Executing it without lying to yourself

Getting the posture right is necessary, not sufficient. Per shape the pipeline runs:

1. **Transit** — a joint-space plan (OMPL RRTConnect) to the chosen configuration at an _approach pose_, one `approach_distance` back along `+Z_S`. Backing off along the normal is what stops transits between shapes from dragging the tool across a drawing plane.
2. **Trace** — `computeCartesianPath` through descend → outline → retreat, held on a single IK branch by the jump threshold.
3. **Retime** — and this step is easy to skip and wrong to skip. `computeCartesianPath` interpolates in configuration space and hands back a path that is geometrically correct and **dynamically meaningless**. It gets re-parameterised with TOTG (`TimeOptimalTrajectoryGeneration`) against the arm's real velocity and acceleration limits.
4. **Execute**, then publish the swept tool path as a marker — which is what the magenta line in the screenshot is, and which is how you catch a discrepancy between what you commanded and what the arm did.

If the Cartesian path still comes back short, the next-ranked configuration is tried. That fallback is cheap precisely because the ranking already exists.

## The bug that costs everyone an afternoon

The shape file is read once at launch, but the node also listens on `/shape_tracer/add_shapes` so another node can hand over work at runtime without a restart. That subscription is **`RELIABLE` + `TRANSIENT_LOCAL`**, and that detail is worth writing down loudly:

> A publisher created with the default QoS profile offers `VOLATILE`, which is _incompatible_. DDS refuses the connection and **not one message is delivered.** There is no error at the publisher. You just watch nothing happen.

Transient-local is deliberate here — it means a producer that publishes before the tracer has finished starting up isn't lost. But the failure mode is silent, and "silent" is the expensive word. `ros2 topic info -v /shape_tracer/add_shapes` shows both ends' profiles, and rclpy will log `offering incompatible QoS` if you know to look for it.

This is a recurring shape of ROS 2 bug: the middleware is doing exactly what you configured, the configuration mismatch is invisible from either side in isolation, and the symptom is _absence_. Nothing to grep for. I built the sample publishers with the right QoS baked in so the next person doesn't rediscover it.

## Then, because the pipeline allows it: words

Once shapes can arrive on a topic, a text renderer is just another producer. `word_writer` takes a `std_msgs/String`, lays the text out on a plane in front of the robot, and publishes it to the tracer **one letter at a time**.

{% include figure.liquid loading="eager" path="assets/img/avatar_challenge_alphabet.png" class="img-fluid rounded z-depth-1" zoomable=true caption="The full alphabet, rendered through exactly the same shape pipeline the arm draws with — no second implementation." %}

Three details that made this work better than expected:

**A letter is a batch, not a shape.** A `Shape` is a single pen-down outline, and most capitals aren't one — E is three strokes, B is three, A is two. So every stroke of a letter goes out in one `ShapeArray`, batches are drawn in arrival order, and a batch arriving mid-trace waits its turn. Left-to-right text falls out of that ordering for free; the pacing parameter exists only so a 40-letter sentence doesn't arrive in one burst.

**The glyphs are geometric, not sampled.** Round letters are true circles of radius 50; bowls are circular arcs given by centre, radius and angle rather than by typed endpoints. The tracer samples arcs and circles _exactly_, so a real arc draws visibly better than a polyline pretending to be one. And because arcs are centre-defined, the sampler can reject one whose endpoints disagree about the radius by more than 0.1 mm — which is the kind of error you make constantly when typing endpoints by hand.

**Reachability is checked before publishing, not during.** On a plane at distance `d`, the arm covers a disc of radius `sqrt((max_reach − margin)² − d²)` about the shoulder; the writing area is the rectangle inscribed in that disc. Every letter's ink box gets checked against it, and a failing letter is skipped _by name_. It's deliberately a first-order filter, not an IK check — the redundancy search remains the authority on solvability. What it buys is that a bad configuration fails at the writer with a message naming the letter, instead of halfway through a trace.

Two smaller choices: corner blending is set to 0 for glyphs, because rounding corners takes the point off an A; and `max_segment_length` drops to 2 mm, because a 60 mm letter sampled at the shape file's 4 mm looks faceted.

There's also a `preview_shapes.py` that subscribes to the same topic and renders what it hears into a PNG — so a shape generator can be validated in a second with no simulation running at all. The alphabet image above was made that way.

## What I'd take from this

The geometry, YAML and redundancy code is a library separate from the ROS node, so all of it is testable without a running `move_group` — unit conversion, every primitive kind, arc direction and large-arc handling, the B-spline convex-hull property, that blending actually removes the 90° tangent jumps of a square, and that every waypoint lands on the plane with the tool normal to it. That separation is what made the redundancy scoring tractable to iterate on.

But the part I keep coming back to is the ranking table. **Redundancy resolution is not a solved sub-problem you delegate to the IK solver.** The solver's job is to find _a_ solution; it has no way to know that the posture it found dies at 55% of an outline it was never shown. The only thing that knows is a dry run.

More generally: when a system gives you slack, that slack becomes a decision, and if you don't make it deliberately, some component further down makes it for you on the basis of much less information. The 7th joint is the clearest example I've hit of that in a while — but it's the same reason greedy waypoint-by-waypoint planning disappoints in general. **Local optimality with no lookahead is just a well-dressed way of getting stuck.**
