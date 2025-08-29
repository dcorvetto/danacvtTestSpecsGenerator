# UI Specification: Scene Members

## 1. Overview
The "Scene Members" screen allows users to manage and assign devices to a specific scene. The primary goal is to provide an intuitive interface for users to view current members, search for devices, and add or remove devices from the scene. This screen enhances user experience by simplifying device management within scenes.

## 2. Layout & Major Components
- **Header**
  - Title: "Scene Members"
  - Back button: Navigates to the previous screen
  - Exit button: Closes the current screen

- **Search Bar**
  - Input field: Placeholder text "Search by name, ID or MAC address"
  - Clear button: Clears the search input

- **Members Section**
  - Title: "MEMBERS"
  - Display: List of currently assigned devices (e.g., "0" if none are assigned)
  - Button: "Press to start assigning members to the scene"

- **Available Devices Section**
  - Title: "AVAILABLE DEVICES"
  - Display: List of devices available for assignment (e.g., "12" if twelve devices are available)
  - Each device entry includes:
    - Device ID
    - Device name (with potential truncation for longer names)

## 3. Interaction Flows
1. **Navigating Back/Exit**
   - User clicks the back button to return to the previous screen.
   - User clicks the exit button to close the screen.

2. **Searching for Devices**
   - User types in the search bar.
   - The list of available devices updates in real-time based on the search query.

3. **Assigning Devices**
   - User selects a device from the "AVAILABLE DEVICES" list.
   - The selected device is moved to the "MEMBERS" section.

4. **Removing Devices**
   - User selects a device from the "MEMBERS" section.
   - The device is removed from the scene.

## 4. States & Empty/Error Handling
- **Empty States**
  - If no members are assigned, display "No members assigned" in the "MEMBERS" section.
  - If no available devices are found, display "No available devices" in the "AVAILABLE DEVICES" section.

- **Error Handling**
  - If a search yields no results, display "No devices found matching your search."
  - Provide feedback for successful or failed assignments (e.g., "Device added successfully" or "Error adding device").

## 5. Accessibility (a11y)
- Ensure all interactive elements are keyboard navigable.
- Use ARIA labels for screen readers on buttons and input fields.
- Provide sufficient color contrast for text and background.
- Include alt text for any icons or images used.

## 6. Data & Validation Rules
- **Search Input**
  - Accepts alphanumeric characters, spaces, and special characters (e.g., hyphens).
  - Triggers search on input change.

- **Device Assignment**
  - Validate that the device is not already a member before assignment.
  - Ensure that the maximum number of members per scene is not exceeded (if applicable).

## 7. Telemetry/Analytics
- Track user interactions:
  - Number of searches performed.
  - Devices assigned and removed.
  - Time spent on the "Scene Members" screen.
- Monitor error rates for device assignments and searches.

## 8. Open Questions
- What is the maximum number of devices that can be assigned to a scene?
- Are there specific device types that should be filtered out from the "AVAILABLE DEVICES" list?
- Should there be a confirmation dialog before removing a device from the scene?
