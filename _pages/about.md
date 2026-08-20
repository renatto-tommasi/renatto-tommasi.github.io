---
layout: about
title: about
permalink: /
subtitle: Full Stack Robotics Engineer · <a href='https://euroknows.com/'>European Knowledge Centre</a>, Budapest

profile:
  align: right
  image: prof_pic.jpg
  image_circular: false # crops the image to make it circular
  more_info: >
    <p>Budapest, Hungary</p>
    <p>Open to roles in 🇲🇽 🇨🇭 🇪🇸 🇺🇸</p>

selected_papers: true # includes a list of papers marked as "selected={true}"
social: true # includes social icons at the bottom of the page

announcements:
  enabled: true # includes a list of news items
  scrollable: true # adds a vertical scroll bar if there are more than 3 news items
  limit: 5 # leave blank to include all the news in the `_news` folder

latest_posts:
  enabled: true # turn on if you decide to blog
  scrollable: true # adds a vertical scroll bar if there are more than 3 new posts items
  limit: 3 # leave blank to include all the blog posts
---

I'm a **Full Stack Robotics Engineer** at the [European Knowledge Centre](https://euroknows.com/) in Budapest. My work keeps landing in strange places: a **point-of-care blood analyser** being qualified to fly on the **International Space Station**, and an **autonomous disinfection robot** finding its own way down **hospital corridors**.

Those two have almost nothing in common on paper. In practice they demand the same thing — a machine that has to work unattended, in an environment that will not cooperate, where nobody is coming to reset it. Chasing that problem across as many domains as will have me is more or less my whole approach to robotics: I'd rather understand the full stack, from the sensor driver up to the mission requirement, than own one clean layer of it.

Day to day I own the **perception and localization stack** of an autonomous ground vehicle in **C++17, Python and ROS 2** — sensor bringup and intrinsic/extrinsic calibration, **multi-camera visual odometry and SLAM**, depth and point-cloud processing, free-space and obstacle estimation, and **multi-sensor fusion through factor-graph optimization on SE(3)** ([GTSAM](https://gtsam.org/)), squeezed onto **NVIDIA Jetson** edge hardware. Fusing four fisheye cameras with RGB-D and wheel odometry cut our angular drift by **95%**. I'm most useful in the unglamorous part: bisecting a stack across drivers, timing, networking and geometry to find where reality and the math disagree — then building the **Isaac Sim** twins, ROS-bag replay and Foxglove tooling that prove the fix holds in the field.

On the space side I'm **Payload Systems Engineer** for the prime contractor on that **ESA ISS payload**, leading the consortium's engineering effort with **Airbus Defence and Space** under ECSS toward Preliminary Design Review. Before that I led the **medical-AI team** for **HUNOR**, the programme that flew a Hungarian astronaut to the ISS, building a cuffless blood-pressure estimator and a denoising filter for the Astroskin biometric suit out of genuinely noisy wearable data.

I hold an M.Sc. in **Intelligent Field Robotics Systems** ([IFRoS](https://ifrosmaster.org/)) — an **Erasmus Mundus** joint master's split between the Universitat de Girona and the University of Zagreb — and before that a mechatronics degree spanning Monterrey and Mannheim, which is where the habit of reaching for a soldering iron before a debugger comes from.

Right now I'm working toward end-to-end **Vision-Language-Action** architectures for mobile robots, supervising two industrial M.Sc. theses that are merging into one: vision-language models for semantic localization, and behaviour cloning with actor–critic refinement in Nav2. I care about systems that aren't just accurate in a paper but robust on real hardware.

Outside the lab I'm a triathlete; the training discipline tends to leak into how I approach engineering.

Feel free to look through my [publications](/publications/) and [projects](/projects/), or get in touch via the links below.
