# Photo Tool: Rename and Convert v1.0

Photo Tool is a user‐friendly desktop application built with `CustomTkinter` designed to simplify common photo management tasks. It allows you to **rename multiple image files** based on various criteria and **convert RAW camera files to JPG** format, including an option to combine both processes.

---

## Features

-   **Batch Renaming:**
    -   Rename multiple files or all files within a selected folder.
    -   Choose a new base name for your files.
    -   Sort files before renaming by:
        -   **Alphabetical order**
        -   **Creation date**
        -   **Date taken (EXIF data)** for accurate chronological ordering.
-   **RAW to JPG Conversion:**
    -   Convert various RAW camera formats (e.g., `.ARW`, `.CR2`, `.NEF`, `.DNG`) to high‐quality JPGs.
    -   Automatically rotates converted JPGs based on EXIF orientation data.
    -   Exports JPGs to a dedicated `exported_jpg` subfolder within the source directory.
-   **Combined Process:**
    -   Perform renaming and RAW to JPG conversion in a single, streamlined operation.
    -   RAW files are first renamed, then converted, ensuring consistency.
-   **Intuitive User Interface:**
    -   Clean and modern interface powered by `CustomTkinter`.
    -   Tabbed navigation for easy switching between renaming and conversion functionalities.
    -   Real-time status logging to keep you informed about ongoing operations.
    -   "Open Folder" button in completion dialog for quick access to processed files.
-   **Cross-Platform Compatibility:**
    -   Designed to work on Windows, macOS, and Linux.

---

## Supported RAW Formats

The application supports a wide range of common RAW camera formats, including but not limited to:

`.ARW`, `.CR2`, `.CR3`, `.NEF`, `.DNG`, `.ORF`, `.RAF`, `.PEF`, `.RW2`, `.SRW`, `.KDC`, `.DCR`, `.MRW`, `.3FR`

---

## Installation

### Prerequisites

Before running the application, ensure you have Python 3.8+ installed on your system.

### Install Dependencies

You can install all necessary Python packages using `pip`:

```bash
pip install customtkinter Pillow exifread rawpy
```

## How to Use

1. **Rename Files**
   - Open the "Rename Files" tab.
   - Click "Select Files" to choose individual files, or "Select Folder" to process all files in a directory.
   - Enter your desired "New base name" (e.g., `Vacation_2023`).
   - Choose a "Sorting Option": "Alphabetically", "Creation Date", or "Date Taken (EXIF)".
   - (Optional) Check "Combine processes: Rename and convert RAW to JPG" if you want to rename your RAW files and then convert them to JPGs.
   - Click "Rename Files" to start the process.

2. **Convert RAW to JPG**
   - Open the "Convert RAW to JPG" tab.
   - Click "Select Folder with RAW Files" and choose the directory containing your RAW images.
   - Click "Start Conversion (RAW to JPG only)".
   - Converted JPGs will be saved in a new `exported_jpg` subfolder within your selected RAW folder.

**Status Log**

The application provides a detailed status log at the bottom of the window, showing the progress and any messages during operations.

## Development

### Running the Application

To run the application, execute the `main.py` file:

```bash
python main.py
```

### Project Structure

- **FileToolApp:** The main application class.
- **`__init__`:** Initializes the UI and sets up tabs.
- **`_create_rename_tab_ui`:** Builds the UI for the rename tab.
- **`_create_raw_to_jpg_tab_ui`:** Builds the UI for the RAW conversion tab.
- **`_select_rename_files`, `_select_rename_folder`:** Handlers for file/folder selection for renaming.
- **`_get_exif_date`:** Helper to extract EXIF original date.
- **`_rename_files_task`:** Core logic for renaming, run in a separate thread.
- **`_rename_files_threaded`:** Initiates the renaming in a thread.
- **`_run_combined_or_rename_task`:** Manages combined rename and convert logic.
- **`_select_raw_folder_for_conversion`:** Handler for RAW folder selection.
- **`_rotate_image_based_on_exif`:** Rotates image based on EXIF orientation.
- **`_process_single_raw_image`:** Processes a single RAW file.
- **`_start_raw_conversion_threaded`:** Initiates RAW conversion in a thread.
- **`_run_raw_conversion_task`:** Core logic for RAW conversion, run in a separate thread.
- **`_perform_raw_conversion_task`:** Unified function for RAW conversion.
- **`log_message`:** Thread‐safe logging to the status text box.
- **`_open_folder_in_explorer`:** Opens a given folder in the system's file explorer.
- **`_show_completion_dialog`:** Custom dialog for operation completion with folder opening option.

## Contributing

Feel free to fork the repository, open issues, or submit pull requests if you have suggestions for improvements or bug fixes.
