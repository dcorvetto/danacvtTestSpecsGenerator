# UI Specification: Scene Members

## 1. Overview
The "Scene Members" screen allows users to manage and assign devices to a specific scene. The primary goal is to provide a clear and intuitive interface for users to search for, view, and select available devices to be included in the scene. This screen aims to enhance user experience by simplifying device management and ensuring efficient scene configuration.

## 2. Layout & Major Components
- **Header**
  - Title: "Scene Members"
  - Back Button: Navigates to the previous screen
  - Exit Button: Closes the scene management interface

- **Search Bar**
  - Input field: "Search by name, ID or MAC address"
  - Placeholder text: Guides users on what to input

- **Members Section**
  - Title: "MEMBERS"
  - Count Display: Shows the number of currently assigned members (e.g., "0")
  - Button: "Press to start assigning members to the scene"

- **Available Devices Section**
  - Title: "AVAILABLE DEVICES"
  - Count Display: Shows the number of available devices (e.g., "12")
  - List of Devices: Displays each device with the following attributes:
    - Device ID (e.g., [1A-331]-190B-XFAC)
    - Device Name (e.g., "Longer name check")
    - Selection Checkbox: Allows users to select devices for assignment

## 3. Interaction Flows
1. **Navigating to Scene Members**
   - User taps on the "Scene Members" option from the main menu.

2. **Searching for Devices**
   - User enters text in the search bar.
   - The list of available devices filters in real-time based on the input.

3. **Assigning Devices to Scene**
   - User selects one or more devices using checkboxes.
   - User taps the "Press to start assigning members to the scene" button to confirm selection.

4. **Exiting the Screen**
   - User taps the back or exit button to return to the previous screen or close the interface.

## 4. States & Empty/Error Handling
- **Empty State**
  - If no devices are available, display a message: "No available devices to assign."
  
- **Error Handling**
  - If a search yields no results, display: "No devices found matching your search."
  - If an error occurs during assignment, show an error message: "Unable to assign devices. Please try again."

## 5. Accessibility (a11y)
- Ensure all interactive elements (buttons, checkboxes) are keyboard navigable.
- Use ARIA labels for screen readers to describe the purpose of buttons and input fields.
- Provide sufficient color contrast for text and background elements.
- Include focus indicators for all interactive components.

## 6. Data & Validation Rules
- **Search Input Validation**
  - Accepts alphanumeric characters and special characters (e.g., hyphens).
  - Minimum input length: 1 character.

- **Device Selection**
  - Users can select multiple devices.
  - At least one device must be selected to proceed with assignment.

## 7. Telemetry/Analytics
- Track user interactions with the search bar (e.g., search queries, number of searches).
- Monitor the number of devices assigned to scenes.
- Log errors encountered during device assignment for future analysis.

## 8. Open Questions
- What specific actions should be taken if a user tries to assign a device that is already part of another scene?
- Should there be a limit on the number of devices that can be assigned to a single scene?
- How should we handle device status updates (e.g., offline devices) in the available devices list?
