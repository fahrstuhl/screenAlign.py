# screenAlign.py
Simple script to automate multi-monitor alignment with xrandr, because xrandr doesn't support aligning two side-by-side screens at the bottom.

Example usage:

```
#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
from screenAlign import Layout

l = Layout(defaultMonitor='LVDS1')
l.setRightOfBottom()
```
