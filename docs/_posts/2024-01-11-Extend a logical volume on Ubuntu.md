---
layout: "default"
title: " Extend a logical volume on Ubuntu"
comments: true
date: "2024-01-11"
categories: tils
---

# TIL: How to Extend a Logical Volume on Ubuntu

1. **Identify the LVM setup**  
   - `lsblk` shows logical volumes (e.g., `lv_var` mapped to `/var`).
   - `lvdisplay` verifies details, like LV Path `/dev/VolGroup00/lv_var`.

2. **Resize the Physical Volume**  
   - Use `sudo pvresize /dev/xvdf` (or the relevant device name) to claim the extra disk space.

3. **Extend and Grow in One Step**  
   - For XFS (and many other filesystems), `lvextend -r -L +100G /dev/VolGroup00/lv_var` automatically resizes both the LV and the filesystem.

4. **Finding the Device Name**  
   - `cat /proc/partitions` lists partitions and sizes (e.g., `/dev/nvme1n1` might be your new disk to `pvresize`).


[Also available at the Wordpress link](https://ranjanmarathe.wordpress.com/2023/12/11/extend-a-logical-volume-on-ubuntu/)

Thanks [Nagendra Sahni](https://www.linkedin.com/in/nagendra-sahni-a6a319191/) for teaching me this technique on a deadline and reviewing the draft. 
