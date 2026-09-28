SNAP_IMAGE_FILES = \
									 src/snapshots/*.snap \


docs/demo_animation.png: $(SNAP_IMAGE_FILES)
	docs/snap_to_apng.py  $(SNAP_IMAGE_FILES) $@
