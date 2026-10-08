SCRIPT_FILE_NAME = docs/snap_to_apng.py

SNAP_IMAGE_FILES = \
									 src/snapshots/*_demo_*.snap \


docs/demo_animation.png: $(SCRIPT_FILE_NAME) $(SNAP_IMAGE_FILES)
	docs/snap_to_apng.py  $(SNAP_IMAGE_FILES) $@


clean:
	rm docs/demo_animation.png
