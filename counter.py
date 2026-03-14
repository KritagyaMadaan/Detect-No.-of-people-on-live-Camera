class PeopleCounter:
    """
    Maintains track history, line crossing logic,
    and actual count stats processing.
    """
    def __init__(self, line_y, margin=30):
        # Coordinates for our virtual crossing line
        self.line_y = line_y
        self.margin = margin
        
        self.tracked_history = {} # Maps ID -> list of center points [y0, y1, ...]
        
        # State counts
        self.total_entries = 0
        self.total_exits = 0

    def update_and_count(self, tracks):
        """
        Takes the current tracking states and calculates line crossings.
        
        Args:
            tracks: list of DeepSORT track objects
            
        Returns:
            int: Number of currently visible tracked and confirmed persons.
        """
        current_count = 0

        for track in tracks:
            # We skip unconfirmed tracking details to avoid false positives 
            if not track.is_confirmed() or track.time_since_update > 1:
                continue
            
            current_count += 1
            track_id = track.track_id
            
            # Fetch bounding box
            ltrb = track.to_ltrb() # left, top, right, bottom
            x1, y1, x2, y2 = map(int, ltrb)
            
            # Use bounding box center to define trajectory point
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            if track_id not in self.tracked_history:
                self.tracked_history[track_id] = []
            
            # Maintain a bounded list to avoid huge memory usage
            self.tracked_history[track_id].append(center_y)
            if len(self.tracked_history[track_id]) > 50:
                self.tracked_history[track_id] = self.tracked_history[track_id][-50:]

            # If enough history is present, verify crossing
            if len(self.tracked_history[track_id]) >= 2:
                prev_y = self.tracked_history[track_id][-2]
                curr_y = self.tracked_history[track_id][-1]

                # Crossing logic: 
                # Check crossing from top to bottom
                if prev_y < self.line_y and curr_y >= self.line_y:
                    self.total_entries += 1
                    
                # Check crossing from bottom to top
                elif prev_y > self.line_y and curr_y <= self.line_y:
                    self.total_exits += 1

        # We can also clean up old tracks that disappeared to clean memory
        
        return current_count

    def update_line(self, line_y):
        self.line_y = line_y
