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

3. **Extend the Logical Volume**  
   - Run `lvextend -L +100G /dev/VolGroup00/lv_var` to add more storage.

4. **Grow the Filesystem**  
   - For XFS: `sudo xfs_growfs /dev/VolGroup00/lv_var`.

5. **Finding the Device Name**  
   - `cat /proc/partitions` lists partitions and sizes (e.g., `/dev/nvme1n1` is a disk you might want to resize with `pvresize /dev/nvme1n1`).

---

**Q:** How might these steps differ if you’re dealing with a RAID array or ephemeral storage on AWS? Could ephemeral storage complicate long-term volume expansions?

[Also available on](https://ranjanmarathe.wordpress.com/2023/12/11/extend-a-logical-volume-on-ubuntu/)
