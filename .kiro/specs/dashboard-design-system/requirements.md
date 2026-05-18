# Requirements Document

## Introduction

This document defines the design system requirements for the Science Gates Custom Dashboard. The design system establishes consistent, reusable UI patterns for all dashboard components including sidebar navigation, topbar, statistics cards, CRUD list pages, create/edit forms, data tables, filters, empty states, and mobile behavior. The system is built with Django Templates, Tailwind CSS, and Alpine.js with full Arabic RTL support. It prioritizes calm, minimal, elegant, and professional aesthetics using flat colors from CSS variables, balanced white space, and consistent typography.

## Glossary

- **Design_System**: The collection of reusable UI components, patterns, spacing rules, and color tokens that ensure visual consistency across the Custom Dashboard
- **Dashboard_Shell**: The persistent layout structure containing the Sidebar, Topbar, and main content area
- **Sidebar**: The fixed right-side vertical navigation panel providing access to all dashboard sections
- **Topbar**: The horizontal header bar at the top of the main content area displaying page context and actions
- **Statistics_Card**: A compact visual component displaying a single metric with label, value, and optional icon
- **CRUD_List_Page**: A standardized page layout for displaying, searching, and filtering collections of content items
- **Form_Page**: A standardized page layout for creating or editing content entities
- **Data_Table**: A structured tabular component for displaying rows of content with sortable columns and actions
- **Filter_Bar**: A horizontal section containing search inputs, dropdowns, and action buttons for narrowing displayed data
- **Empty_State**: A placeholder UI displayed when a list or section contains no data
- **CSS_Variable**: A custom property declared in :root used for all color values across the dashboard
- **Breakpoint**: A screen width threshold where layout adapts (mobile: <768px, tablet: 768-1024px, desktop: >1024px)
- **Component_Template**: A Django template partial (include) representing a single reusable UI element

---

## Requirements

### Requirement 1: CSS Variable Color Token System

**User Story:** As a Content_Admin, I want the dashboard to use a consistent color palette defined through CSS variables, so that the interface feels cohesive and colors can be updated from a single source.

#### Acceptance Criteria

1. THE Design_System SHALL define all dashboard colors as CSS variables in the :root selector
2. THE Design_System SHALL provide semantic color tokens: primary, primary-hover, secondary, success, danger, warning, info, border, background-light, background-dark, text-primary, text-secondary, text-muted
3. THE Design_System SHALL use CSS variables for all brand and semantic color values in dashboard components, while permitting Tailwind neutral utility classes (gray-50 through gray-900) for structural backgrounds, borders, and text shading that do not represent brand or semantic meaning
4. THE Design_System SHALL use flat colors without gradients for all surfaces and elements
5. THE Design_System SHALL ensure a minimum contrast ratio of 4.5:1 between normal-size text (below 18pt regular or 14pt bold) and its background color, and a minimum contrast ratio of 3:1 for large text (18pt regular or 14pt bold and above)
6. THE Design_System SHALL provide distinct color tokens for interactive states (default, hover, focus, active, disabled) for buttons, navigation items, links, and form inputs

### Requirement 2: Spacing and Layout Scale

**User Story:** As a Content_Admin, I want consistent spacing throughout the dashboard, so that the interface feels balanced and professional with adequate breathing room.

#### Acceptance Criteria

1. THE Design_System SHALL define a spacing scale using Tailwind's default spacing values (4px base unit) with the following levels applied across the dashboard: 4px (1), 8px (2), 12px (3), 16px (4), 24px (6), 32px (8)
2. THE Design_System SHALL apply p-6 padding within cards and containers at page level, and p-4 padding within nested or inline components (e.g., table cells, compact filter inputs, badge groups)
3. THE Design_System SHALL apply gap-6 between grid items at page level, and gap-4 between grid items within cards or nested containers
4. THE Design_System SHALL apply mb-6 margin between consecutive page sections within the main content area
5. THE Design_System SHALL apply a minimum spacing of 8px (space-y-2) between stacked content elements within a section (e.g., label to input, heading to description, icon to text)
6. THE Design_System SHALL define a maximum content width of max-w-4xl (896px) for form pages to constrain line lengths on viewports wider than 896px

### Requirement 3: Sidebar Navigation Component

**User Story:** As a Content_Admin, I want a clear, organized sidebar navigation, so that I can quickly access any section of the dashboard without confusion.

#### Acceptance Criteria

1. THE Sidebar SHALL be positioned on the right side of the viewport in RTL layout
2. THE Sidebar SHALL have a fixed width of 256px (w-64) on desktop viewports
3. THE Sidebar SHALL display the platform logo (max-height 40px) and platform name at the top with consistent padding (p-6)
4. THE Sidebar SHALL organize navigation links into labeled sections (Content, Messages, SEO, Administration)
5. THE Sidebar SHALL display section headers as uppercase text-xs labels colored with the text-muted CSS variable
6. THE Sidebar SHALL display navigation items with an SVG icon (w-5 h-5) and Arabic text label
7. WHEN the current page URL matches a navigation item's target path, THE Sidebar SHALL highlight that item with a distinct background color and text color using CSS variables
8. WHEN a Content_Admin hovers over a navigation item, THE Sidebar SHALL display a background color change using CSS variables with transition-colors duration-200
9. THE Sidebar SHALL display a user profile section at the bottom with the user's name, role label, and a logout button that navigates to the login page
10. THE Sidebar SHALL remain fixed (position: fixed) and visible while the main content area scrolls
11. THE Sidebar SHALL use a left border (in RTL) to visually separate it from the main content area
12. IF a Content_Admin does not have the required permission for a navigation section, THEN THE Sidebar SHALL hide that entire section including its header and navigation items
13. THE Sidebar SHALL support keyboard navigation, allowing focus traversal through all navigation items using the Tab key with a visible focus indicator
14. WHEN a Content_Admin clicks the logout button, THE Sidebar SHALL end the user session and redirect to the login page

### Requirement 4: Topbar Header Component

**User Story:** As a Content_Admin, I want a clear page header showing where I am and what actions are available, so that I always have context about the current page.

#### Acceptance Criteria

1. THE Topbar SHALL span the full width of the main content area
2. THE Topbar SHALL display the current page title using text-2xl font-bold styling
3. THE Topbar SHALL optionally display a page description or subtitle below the title using text-sm text-muted styling, limited to a single line of text
4. THE Topbar SHALL optionally display up to 3 primary action buttons aligned to the left side (in RTL), following the button component variants defined in the Design_System
5. THE Topbar SHALL have a bottom border using the CSS variable border color to visually separate it from page content
6. THE Topbar SHALL use a white background with consistent horizontal padding (px-8) and vertical padding (py-4)
7. THE Topbar SHALL remain at the top of the main content area (not fixed, scrolls with content)
8. WHILE the viewport width is below 768px, THE Topbar SHALL stack title and action buttons vertically with gap-3 spacing between them
9. THE Topbar SHALL arrange the page title and description on the right side and action buttons on the left side (in RTL) using a flex layout with vertical centering

### Requirement 5: Statistics Card Component

**User Story:** As a Content_Admin, I want to see key metrics displayed in clear, scannable cards, so that I can quickly understand the current state of the platform.

#### Acceptance Criteria

1. THE Statistics_Card SHALL display a text label (maximum 50 characters) describing the metric above the metric value
2. THE Statistics_Card SHALL display the metric value in large, bold typography (text-3xl font-bold), supporting numeric values up to 7 digits and text values up to 10 characters
3. WHERE an icon is provided, THE Statistics_Card SHALL display the icon (w-5 h-5) centered inside a colored background circle (w-10 h-10 rounded-full) aligned opposite to the text content in RTL layout
4. THE Statistics_Card SHALL use a white background with rounded corners (rounded-lg), shadow-sm, and internal padding (p-6)
5. WHERE a category indicator is configured, THE Statistics_Card SHALL display a colored right border (border-r-4) using a CSS variable color token
6. THE Statistics_Card SHALL use CSS variable colors for the category border and icon background
7. THE Statistics_Card SHALL be arranged in a responsive grid: 1 column below 768px, 2 columns between 768px and 1024px, and 4 columns above 1024px
8. THE Statistics_Card SHALL maintain equal height within the same row regardless of content length

### Requirement 6: CRUD List Page Layout

**User Story:** As a Content_Admin, I want list pages to follow a consistent structure, so that I can manage any content type with the same familiar interface.

#### Acceptance Criteria

1. THE CRUD_List_Page SHALL follow a consistent vertical structure: page header, filter bar, data table, pagination
2. THE CRUD_List_Page SHALL display a page header with title, description, and primary "Add New" action button
3. THE CRUD_List_Page SHALL display the Filter_Bar in a white card above the data table
4. THE CRUD_List_Page SHALL display content items in a Data_Table component
5. IF the total number of items exceeds the page limit of 20 items per page, THEN THE CRUD_List_Page SHALL display pagination controls below the data table
6. IF no items exist in the content collection, THEN THE CRUD_List_Page SHALL display an Empty_State component in place of the Filter_Bar, Data_Table, and pagination sections
7. THE CRUD_List_Page SHALL maintain consistent spacing between all sections (space-y-6)
8. IF applied filters return no matching items, THEN THE CRUD_List_Page SHALL display the Filter_Bar with current filter values and an Empty_State component in place of the Data_Table indicating no results match the current filters

### Requirement 7: Data Table Component

**User Story:** As a Content_Admin, I want data tables to be readable and functional, so that I can scan content quickly and take actions on individual items.

#### Acceptance Criteria

1. THE Data_Table SHALL display content in a white card with rounded corners (rounded-lg) and subtle shadow
2. THE Data_Table SHALL display column headers in a gray background row (bg-gray-50) with right-aligned text for RTL
3. THE Data_Table SHALL display column headers in small, semibold, uppercase text
4. THE Data_Table SHALL display rows with consistent padding (px-6 py-4) and dividing borders between rows
5. WHEN a Content_Admin hovers over a table row, THE Data_Table SHALL display a background highlight (hover:bg-gray-50)
6. THE Data_Table SHALL display an actions column with edit and delete icon buttons for each row, where the edit button navigates to the item's edit page and the delete button navigates to the item's delete confirmation page
7. THE Data_Table SHALL display status values using colored badge components as defined in the Badge and Status Indicator Component
8. WHEN the viewport width is narrower than the table content width, THE Data_Table SHALL enable horizontal scrolling to allow access to all columns
9. THE Data_Table SHALL display clickable item names as links styled with the CSS variable primary color, leading to the item's edit page
10. THE Data_Table SHALL use consistent text sizing (text-sm) for all cell content
11. THE Data_Table SHALL use semantic HTML table elements (table, thead, tbody, th, td) with appropriate scope attributes on header cells for screen reader accessibility
12. THE Data_Table SHALL ensure all action buttons are keyboard-focusable and display a visible focus indicator using the CSS variable primary color

### Requirement 8: Filter Bar Component

**User Story:** As a Content_Admin, I want consistent filtering controls, so that I can quickly narrow down content lists to find what I need.

#### Acceptance Criteria

1. THE Filter_Bar SHALL be contained in a white card with padding (p-6) and rounded corners (rounded-lg)
2. THE Filter_Bar SHALL arrange filter inputs in a responsive grid (1 column on viewports below 768px, 2 columns on viewports between 768px and 1024px, 3 columns on viewports above 1024px)
3. THE Filter_Bar SHALL provide a text search input with placeholder text listing the searchable field names, accepting a maximum of 200 characters
4. THE Filter_Bar SHALL provide dropdown select inputs for categorical filters (status, type, category) with a default empty option indicating no selection
5. THE Filter_Bar SHALL provide a submit button to apply filters and a secondary reset button to clear all filter values
6. WHEN the Content_Admin submits the filter form, THE Filter_Bar SHALL preserve the selected filter values in the URL query string
7. WHEN the Content_Admin clicks the reset button, THE Filter_Bar SHALL clear all input values and navigate to the base list URL without query parameters
8. THE Filter_Bar SHALL display all inputs with consistent styling: border, rounded-lg, focus ring using CSS variable primary color
9. THE Filter_Bar SHALL support RTL text direction in all input fields

### Requirement 9: Create and Edit Form Page Layout

**User Story:** As a Content_Admin, I want form pages to be clean and organized, so that I can create and edit content without feeling overwhelmed.

#### Acceptance Criteria

1. THE Form_Page SHALL organize form fields into visually separated sections, each with an Arabic heading displayed in section heading typography (text-lg font-semibold) and a bottom border or spacing (mb-6) separating it from the next section
2. THE Form_Page SHALL display form fields with labels above inputs (stacked layout)
3. THE Form_Page SHALL display required field indicators using an asterisk colored with the CSS variable danger color adjacent to the field label
4. THE Form_Page SHALL display help text below inputs in small muted text (text-xs text-muted)
5. THE Form_Page SHALL display validation errors below the relevant input in red text with a red border on the input
6. THE Form_Page SHALL display the submit button area at the bottom of the form, remaining visible via sticky positioning (sticky bottom-0) when the form content exceeds the viewport height
7. THE Form_Page SHALL use consistent input styling: full width, border, rounded-lg, padding (px-4 py-2), focus ring with CSS variable primary color
8. THE Form_Page SHALL limit form content width to max-w-4xl on viewports wider than 1024px to maintain readable line lengths
9. THE Form_Page SHALL support inline formsets for related entities (faculties, courses, FAQ items) with an add button to append a new empty item and a remove button on each item, managed via Alpine.js without page reload
10. THE Form_Page SHALL display a cancel button alongside the submit button linking back to the list page, styled as a secondary button variant
11. IF a form submission fails validation, THEN THE Form_Page SHALL preserve all entered data and scroll to the first error
12. THE Form_Page SHALL visually separate each inline formset item with a border or card container and consistent spacing (space-y-4) between items

### Requirement 10: Empty State Component

**User Story:** As a Content_Admin, I want a helpful message when a section has no content, so that I know the page loaded correctly and understand what action to take next.

#### Acceptance Criteria

1. THE Empty_State SHALL be displayed horizontally centered within the parent container with vertical padding (py-16)
2. THE Empty_State SHALL display an SVG illustration or icon in gray-400 color at a fixed size of w-16 h-16
3. THE Empty_State SHALL display a heading describing the empty condition in Arabic using text-lg font-semibold text-gray-900
4. THE Empty_State SHALL display a description suggesting the next action in Arabic using text-sm text-gray-500, with a maximum length of 120 characters
5. WHERE an action button is configured, THE Empty_State SHALL display a primary-styled action button below the description
6. THE Empty_State SHALL use vertical spacing of space-y-4 (16px) between icon, heading, description, and button
7. THE Empty_State SHALL use muted colors (gray-400 for icon, gray-900 for heading, gray-500 for description)

### Requirement 11: Mobile Responsive Behavior

**User Story:** As a Content_Admin using a tablet, I want the dashboard to adapt to smaller screens, so that I can manage content on mobile devices when needed.

#### Acceptance Criteria

1. WHEN the viewport width is below 768px, THE Sidebar SHALL be hidden by default
2. WHEN the viewport width is below 768px, THE Dashboard_Shell SHALL display a hamburger menu button in the Topbar to toggle Sidebar visibility
3. WHEN the hamburger menu is activated, THE Sidebar SHALL slide in as an overlay from the right side (RTL) with a transition duration of 200ms
4. WHEN the Sidebar overlay is visible, THE Dashboard_Shell SHALL display a backdrop with 50% opacity black background behind the Sidebar and above the main content
5. WHEN the backdrop is tapped, THE Sidebar SHALL close
6. WHEN the viewport width is below 768px, THE Data_Table SHALL enable horizontal scrolling for wide tables
7. WHEN the viewport width is below 768px, THE Filter_Bar SHALL stack all inputs vertically in a single column
8. WHEN the viewport width is below 768px, THE Statistics_Card grid SHALL display cards in a single column
9. WHEN the viewport width is below 768px, THE Topbar SHALL stack title and action buttons vertically with gap-3 spacing
10. THE Dashboard_Shell SHALL use Alpine.js for mobile sidebar toggle state management without page reload
11. WHEN a navigation link in the Sidebar overlay is tapped, THE Sidebar SHALL close and the backdrop SHALL be removed

### Requirement 12: Notification Messages Component

**User Story:** As a Content_Admin, I want clear feedback after performing actions, so that I know whether my action succeeded or failed.

#### Acceptance Criteria

1. THE Design_System SHALL display Django messages as dismissible notification banners below the Topbar, stacked vertically with a gap of 8px between multiple messages
2. THE Design_System SHALL style success messages with a green background tint and green border using CSS variables
3. THE Design_System SHALL style error messages with a red background tint and red border using CSS variables
4. THE Design_System SHALL style info messages with a blue background tint and blue border using CSS variables
5. THE Design_System SHALL style warning messages with a yellow background tint and yellow border using CSS variables
6. THE Design_System SHALL display a dismiss button (X icon) on each notification message, aligned to the left side in RTL layout
7. WHEN a Content_Admin clicks the dismiss button, THE Design_System SHALL remove the notification message from view without page reload using Alpine.js
8. THE Design_System SHALL display notification messages with padding (px-4 py-3), rounded corners (rounded-lg), text-sm font size, and an icon corresponding to the message type
9. THE Design_System SHALL display the message text content within each notification banner with sufficient contrast against the tinted background (minimum 4.5:1 ratio)
10. THE Design_System SHALL assign an ARIA role of "alert" to error and warning messages and a role of "status" to success and info messages

### Requirement 13: Button Component Variants

**User Story:** As a Content_Admin, I want buttons to clearly communicate their purpose through consistent styling, so that I can distinguish primary actions from secondary or destructive ones.

#### Acceptance Criteria

1. THE Design_System SHALL define a primary button variant using the CSS variable primary color as background with white text
2. THE Design_System SHALL define a secondary button variant using a gray-100 background with text-gray-800 text
3. THE Design_System SHALL define a danger button variant using the CSS variable danger color as background with white text
4. THE Design_System SHALL define a ghost button variant with transparent background and CSS variable primary color text
5. WHEN a Content_Admin hovers over a primary button, THE button SHALL display the CSS variable primary-hover color as background
6. WHEN a Content_Admin hovers over a secondary button, THE button SHALL display a gray-200 background
7. WHEN a Content_Admin hovers over a danger button, THE button SHALL display a darker shade of the CSS variable danger color as background
8. WHEN a Content_Admin hovers over a ghost button, THE button SHALL display a gray-100 background while retaining its text color
9. THE Design_System SHALL apply consistent button sizing: padding (px-4 py-2), rounded corners (rounded-lg), font weight (font-medium)
10. THE Design_System SHALL apply cursor-pointer to all interactive button elements
11. THE Design_System SHALL display buttons with transition-colors duration-200 on hover
12. THE Design_System SHALL define a disabled button state with opacity-50 and pointer-events-none

### Requirement 14: Badge and Status Indicator Component

**User Story:** As a Content_Admin, I want status information to be visually distinct and scannable, so that I can quickly identify the state of content items.

#### Acceptance Criteria

1. THE Design_System SHALL define badge components as inline pill-shaped elements (rounded-full, px-2.5 py-0.5)
2. THE Design_System SHALL provide color variants for badges: green (published/success), gray (unpublished/inactive), blue (info), yellow (pending/new), red (error/urgent)
3. THE Design_System SHALL use light background tints with darker text for badge colors (e.g., bg-green-100 text-green-800) maintaining a minimum contrast ratio of 4.5:1 between badge text and badge background
4. THE Design_System SHALL display badges in small text (text-xs) with medium font weight (font-medium)
5. THE Design_System SHALL display a descriptive text label inside each badge that communicates the status without relying on color alone (e.g., "منشور", "مسودة", "جديد")
6. THE Design_System SHALL map each status value to exactly one color variant across all list pages: publish status (published → green, unpublished → gray), lead type (new → yellow, contacted → blue), read status (read → gray, unread → yellow, urgent → red)
7. IF a status value has no defined color mapping, THEN THE Design_System SHALL render the badge using the gray variant as the default fallback

### Requirement 15: Pagination Component

**User Story:** As a Content_Admin, I want clear pagination controls, so that I can navigate through large content lists efficiently.

#### Acceptance Criteria

1. THE Pagination component SHALL be displayed below the Data_Table in a gray footer area (bg-gray-50) with consistent padding (px-6 py-3) and a top border separating it from table rows
2. THE Pagination component SHALL display the current page number and total page count in the format "صفحة [current] من [total]" (Page X of Y)
3. THE Pagination component SHALL provide navigation links: first, previous, next, last
4. IF the current page is the first page, THEN THE Pagination component SHALL disable the "first" and "previous" navigation links with reduced opacity (opacity-50) and no pointer events
5. IF the current page is the last page, THEN THE Pagination component SHALL disable the "next" and "last" navigation links with reduced opacity (opacity-50) and no pointer events
6. THE Pagination component SHALL preserve current filter and search parameters as URL query string values in all pagination links
7. THE Pagination component SHALL style navigation links with a border (border-gray-300), rounded corners (rounded-lg), padding (px-3 py-1), and a hover background color change (hover:bg-gray-100) consistent with the Design_System button styling
8. THE Pagination component SHALL position navigation links on the left side and page info text on the right side using flex justify-between layout (respecting RTL direction)
9. IF the total number of pages is 1 or fewer, THEN THE Pagination component SHALL be hidden

### Requirement 16: Form Input Component Styling

**User Story:** As a Content_Admin, I want form inputs to be clearly visible and easy to interact with, so that data entry is comfortable and error-free.

#### Acceptance Criteria

1. THE Design_System SHALL style text inputs, textareas, and selects with: full width, border (border-gray-300), rounded corners (rounded-lg), padding (px-4 py-2)
2. WHEN a form input receives focus, THE Design_System SHALL display a focus ring using the CSS variable primary color (ring-2 ring-primary)
3. IF a form input has a validation error, THEN THE Design_System SHALL display a red border (border-red-500) and red error text (text-sm) below the input with a top margin of mt-1
4. THE Design_System SHALL display form labels in medium weight text (font-medium) above inputs with small bottom margin (mb-2)
5. THE Design_System SHALL support RTL text direction (dir="rtl") in all text inputs and textareas
6. THE Design_System SHALL style disabled inputs with a gray background (bg-gray-100), reduced opacity (opacity-50), and cursor-not-allowed
7. THE Design_System SHALL style file upload inputs with the same border (border-gray-300), rounded corners (rounded-lg), padding (px-4 py-2), and focus ring as text inputs
8. THE Design_System SHALL display select dropdowns with a custom SVG arrow indicator positioned on the left side in RTL layout
9. THE Design_System SHALL apply transition-colors duration-200 to all form inputs for smooth state changes between default, focus, and error states

### Requirement 17: Card Container Component

**User Story:** As a Content_Admin, I want content sections to be visually grouped in clean containers, so that the interface feels organized and scannable.

#### Acceptance Criteria

1. THE Design_System SHALL define a card component with white background, rounded corners (rounded-lg), shadow-sm, and a 1px border using the CSS variable border color
2. THE Design_System SHALL apply consistent internal padding to cards (p-6)
3. THE Design_System SHALL use cards as the primary container for: filter bars, data tables, form sections, statistics groups, empty states, and notification areas
4. THE Design_System SHALL NOT apply hover effects, shadow transitions, or scale transforms to cards that serve as static layout containers (cards that are not clickable navigation targets)
5. WHERE a card header is enabled, THE Design_System SHALL display a title in text-base font-medium typography followed by a 1px border-bottom separator using the CSS variable border color, with consistent bottom margin (mb-4) between the separator and card body content

### Requirement 18: Icon System Standards

**User Story:** As a Content_Admin, I want icons to be consistent and meaningful throughout the dashboard, so that I can quickly recognize actions and sections.

#### Acceptance Criteria

1. THE Design_System SHALL use inline SVG icons exclusively (no emoji icons, no icon fonts)
2. THE Design_System SHALL use a consistent icon set (Heroicons outline style) throughout the dashboard with a fixed viewBox of "0 0 24 24" for all icons
3. THE Design_System SHALL size icons according to context: w-5 h-5 for sidebar navigation items, w-5 h-5 for empty state icons, w-4 h-4 for table action buttons, and w-4 h-4 for button inline icons
4. THE Design_System SHALL position icons with ml-2 margin from adjacent text in RTL layout for compact contexts (buttons, table actions) and ml-3 for sidebar navigation items
5. THE Design_System SHALL color icons using currentColor to inherit text color from parent elements
6. THE Design_System SHALL use stroke-width="2" consistently for all outline icons
7. THE Design_System SHALL mark decorative icons with aria-hidden="true", and icons that serve as the only indicator of an action SHALL have an accessible label via aria-label on the parent interactive element
8. IF an icon is used without adjacent visible text, THEN THE Design_System SHALL provide a screen-reader-accessible label describing the icon's action or meaning

### Requirement 19: Typography Scale

**User Story:** As a Content_Admin, I want text to be readable and hierarchically clear, so that I can scan content quickly and understand information structure.

#### Acceptance Criteria

1. THE Design_System SHALL define a typography scale with exactly five levels: page title (text-2xl font-bold), section heading (text-lg font-semibold), card title (text-base font-medium), body text (text-sm), helper text (text-xs text-muted)
2. THE Design_System SHALL use the CSS variable text-primary token for primary text, text-secondary token for secondary text, and text-muted token for muted text as defined in the color token system
3. THE Design_System SHALL apply leading-relaxed (1.625) line height to body text and helper text, and leading-normal (1.5) line height to headings and card titles
4. THE Design_System SHALL not change or override the project's existing font family
5. THE Design_System SHALL render all text with dir="rtl" attribute and right-aligned text direction, ensuring Arabic characters display without clipping, overlap, or incorrect glyph joining

### Requirement 20: Delete Confirmation Pattern

**User Story:** As a Content_Admin, I want a clear confirmation step before deleting content, so that I do not accidentally remove important data.

#### Acceptance Criteria

1. WHEN a Content_Admin clicks a delete action, THE Design_System SHALL navigate to a dedicated confirmation page
2. THE confirmation page SHALL display the item name or title in bold text within a warning message identifying what will be deleted, truncated with ellipsis if exceeding 100 characters
3. THE confirmation page SHALL display a warning message stating that the deletion is permanent and cannot be undone
4. THE confirmation page SHALL display a danger-styled confirm button and a secondary cancel button, where the cancel button navigates back to the list page for the item's content type
5. THE confirmation page SHALL use a card container with p-6 padding, centered horizontally on the page with a maximum width of max-w-lg
6. THE Design_System SHALL NOT use JavaScript modal dialogs for delete confirmation
7. WHEN a Content_Admin confirms deletion, THE Design_System SHALL delete the item, redirect to the corresponding CRUD_List_Page, and display a success notification message confirming the item was deleted

---

## Implementation Notes

- All components are implemented as Django template partials ({% include %}) for reusability
- Colors reference CSS variables from :root — no hardcoded hex or rgb values in templates
- Alpine.js handles interactive behavior (mobile sidebar toggle, message dismissal) without page reloads
- No React, Vue, or other JavaScript frameworks
- No gradients, no unnecessary animations — only subtle color transitions (transition-colors duration-200)
- Typography remains unchanged — the existing project font is preserved
- The design system documents patterns already partially established in the existing codebase and standardizes them for consistency
- All components support Arabic RTL layout as the primary direction
- Tailwind CSS utility classes are the primary styling mechanism, with CSS variables for color tokens
