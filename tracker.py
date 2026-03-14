from deep_sort_realtime.deepsort_tracker import DeepSort

class PersonTracker:
    """
    Tracker class utilizing DeepSORT to uniquely track persons
    from YOLO detections.
    """
    def __init__(self, max_age=30, n_init=3, max_cosine_distance=0.3):
        # Initialize DeepSORT instance
        # max_age determines how many frames missed before deleting a track.
        # This helps greatly in tracking under low light or occlusion.
        self.tracker = DeepSort(max_age=max_age,
                                n_init=n_init,
                                max_cosine_distance=max_cosine_distance,
                                nn_budget=100,
                                override_track_class=None,
                                embedder="mobilenet",
                                half=True,
                                bgr=True) 

    def update(self, frame, detections):
        """
        Updates the tracker using the current frame and detections.

        Args:
            frame: A numpy array representing the image frame (BGR).
            detections: List of detections (bbox, score, class)

        Returns:
            A list of tracked objects to be parsed.
        """
        # We pass the detections. Formats required: list of ([left,top,w,h], confidence, detection_class)
        # DeepSORT uses its appearance embedder to find features in the frame for the defined boxes.
        tracks = self.tracker.update_tracks(detections, frame=frame)
        return tracks