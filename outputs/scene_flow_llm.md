# Flow Spec — Scene Members Flow

_Generated: 2025-09-02 18:11_

# Scene Members Flow — UI Specification

## Overview — Purpose and Goals
- Enable users to assign devices or groups as members of a scene.
- Provide clear distinction between assigned members and available devices/groups.
- Support search and filtering by name, ID, or MAC address.
- Allow adding/removing members with clear visual feedback.
- Ensure smooth editing, saving, and cancellation of changes.
- Handle error states gracefully with actionable guidance.

## Layout & Major Components
- **Header Bar:** Back/Cancel, Title ("Scene Members"), Bluetooth status icon, Edit/Done/Save buttons.
- **Search Bar:** Input for filtering by name, ID, or MAC address.
- **Tab Selector:** Toggle between "Devices" and "Groups".
- **Expandable Sections:**
  - Members (assigned devices/groups) with count.
  - Available Devices/Groups with count.
- **List Items:** Icon + name + action button (add/remove).
- **Modal Alerts:** For success and failure feedback.

## Flow Overview
1. Initial view shows members and available devices/groups, Edit button enabled [Screen 1].
2. User taps Edit → switches to edit mode with Cancel/Done buttons, add icons appear [Screen 2].
3. User adds/removes members; members and available lists update dynamically [Screens 3,4].
4. User taps Done → Save button appears, user confirms save or cancels [Screens 5,6].
5. On save success, show confirmation modal [Screen 8].
6. On save failure, show error modal with instructions [Screen 7].
7. User can switch tabs between Devices and Groups anytime.

## Per-screen Components

### [Screen 1] Initial View (Read-only)
- Header: Back, Title, Bluetooth icon, Edit button.
- Search input (disabled or enabled).
- Tabs: Devices (active), Groups (inactive).
- Members section: collapsible, count displayed, message prompting to Edit if empty.
- Available Devices section: collapsible, count displayed.
- List items: icon (device light bulb), name text, no action buttons.

### [Screen 2] Edit Mode (Adding Members)
- Header: Cancel, Title, Bluetooth icon, Done button.
- Search input (enabled).
- Tabs: Devices (active), Groups (inactive).
- Members section: collapsible, count displayed, empty message.
- Available Devices section: collapsible, count displayed.
- List items: icon (device light bulb), name text, green circular plus button on left.

### [Screen 3] Edit Mode (After Adding Member)
- Header: Cancel, Title, Bluetooth icon, Save button.
- Search input (enabled).
- Tabs: Devices (active), Groups (inactive).
- Members section: collapsible, count updated, list shows added members.
- Available Devices section: collapsible, count updated.
- List items in Members: icon, name, red circular minus button on left.
- List items in Available Devices: icon, name, green plus button.

### [Screen 4] Edit Mode (Multiple Members Added)
- Same as Screen 3 with multiple members in Members list.

### [Screen 5] Edit Mode with Groups Tab
- Header: Cancel, Title, Bluetooth icon, Save button.
- Search input (enabled).
- Tabs: Devices (inactive), Groups (active).
- Members section: collapsible, count displayed.
- Available Groups section: collapsible, count displayed.
- List items: icon (group icon), name text, add/remove buttons as per membership.

### [Screen 6] Edit Mode with Groups Tab, after changes
- Same as Screen 5 with updated members and available groups.

### [Screen 7] Error Modal
- Title: "Failed to Set Scene Member(s)"
- Message: Instructions to check range, power, and perform Scene Repair.
- Single "OK" button to dismiss.

### [Screen 8] Success Modal
- Message: "Scene successfully saved."
- Single "OK" button to dismiss.

## Interaction Flow
- Tap **Edit** → enter edit mode, show Cancel/Done, enable add buttons.
- Tap **+** on available device/group → move item to Members list, update counts.
- Tap **-** on member → move item back to Available list, update counts.
- Tap **Done** → switch to Save button.
- Tap **Save** → attempt to save changes.
  - On success → show success modal.
  - On failure → show error modal.
- Tap **Cancel** → discard changes, revert to initial view.
- Search filters lists dynamically by name, ID, or MAC address.
- Tabs switch between Devices and Groups, preserving current edits.

## Validation & Edge Cases
- Prevent adding duplicate members.
- Handle empty members or available lists gracefully with messages.
- Long names truncated with ellipsis but fully readable on focus or accessible readout.
- Search input filters both members and available lists.
- Save button disabled if no changes made.
- Error modal triggers if save fails due to device offline or out of range.
- Confirm discard changes on Cancel if edits made (not shown in mockups, recommend).

## Accessibility
- All buttons and interactive elements have accessible labels (e.g., "Add device [name]", "Remove device [name]").
- Color contrast meets WCAG AA standards (green plus, red minus).
- Keyboard navigable and screen reader friendly.
- Search input labeled with placeholder and accessible name.
- Modal dialogs trap focus and announce content.
- Icons have descriptive alt text or aria-labels.

## General Data & Validation
- Device/group names can be alphanumeric with special characters.
- IDs and MAC addresses searchable as text.
- Member counts update dynamically.
- Bluetooth icon reflects connection status (not detailed here).
- Maximum number of members/groups not specified; UI supports scrolling.

## Telemetry
- Track user actions: Edit tapped, Add/Remove member, Save success/failure, Cancel.
- Log search queries and tab switches.
- Capture error modal triggers with error context.
- Time spent in edit mode.

## Open Questions / Assumptions
- Is there a maximum number of members allowed per scene?
- Should Cancel prompt confirmation if unsaved changes exist?
- Are groups and devices mutually exclusive or can a device be in both lists?
- Should search filter members and available lists separately or combined?
- What is the expected behavior if Bluetooth disconnects mid-edit?
- Are there any performance considerations for very large device/group lists?
- Should long names be fully visible on tap or via tooltip?
- Is there a need for multi-select add/remove or only single item actions?