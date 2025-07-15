import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import math
import exifread
import datetime
import rawpy
import io
from PIL import Image, ExifTags
import threading
import subprocess # For opening folders
import sys # For platform check

class FileToolApp:
    def __init__(self, master):
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.master = master
        master.title("Photo Tool - Rename and Convert")
        master.geometry("800x750") # Increased size for larger fonts
        master.resizable(True, True)

        self.rename_selected_files = []
        self.rename_selected_folder = ""
        self.raw_conversion_folder = ""
        self.last_operation_folder = "" # To store the folder for 'Open Folder' button

        self.tab_view = ctk.CTkTabview(master, corner_radius=10)
        self.tab_view.pack(expand=True, fill="both", padx=20, pady=20)

        self.rename_tab = self.tab_view.add("Rename Files")
        self.raw_to_jpg_tab = self.tab_view.add("Convert RAW to JPG")

        self._create_rename_tab_ui(self.rename_tab)
        self._create_raw_to_jpg_tab_ui(self.raw_to_jpg_tab)

        status_label = ctk.CTkLabel(master, text="Operation Status", font=("Inter", 13, "bold")) # Increased font
        status_label.pack(pady=(15, 5), padx=25, anchor="w") # Increased padding

        status_frame = ctk.CTkFrame(master, corner_radius=10, fg_color=("gray85", "gray25"))
        status_frame.pack(pady=(0, 20), padx=25, fill="both", expand=True)

        self.status_text = ctk.CTkTextbox(status_frame, height=100, state="disabled", wrap="word", corner_radius=8, font=("Inter", 12)) # Increased font
        self.status_text.pack(fill="both", expand=True, padx=10, pady=10)

    def log_message(self, message):
        """Logs a message to the status text box in a thread-safe way."""
        self.master.after(0, lambda: self._update_log_text(message))

    def _update_log_text(self, message):
        """Internal method to update the text box from the main thread."""
        self.status_text.configure(state="normal")
        self.status_text.insert(ctk.END, message + "\n")
        self.status_text.see(ctk.END)
        self.status_text.configure(state="disabled")

    def _open_folder_in_explorer(self, path):
        """Opens the specified folder in the default file explorer."""
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "The folder path is invalid or the folder does not exist.")
            return
        try:
            # For Windows
            if sys.platform == "win32":
                os.startfile(path)
            # For macOS
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            # For Linux
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")
            self.log_message(f"Error opening folder: {e}")


    # --- UI for "Rename Files" Tab ---
    def _create_rename_tab_ui(self, tab):
        # Path label
        self.rename_path_label = ctk.CTkLabel(tab, text="Select files or a folder to rename.", wraplength=550, font=("Inter", 14, "bold"))
        self.rename_path_label.pack(pady=(15, 5), padx=20, fill="x")

        # Info about selected files count
        self.rename_files_count_label = ctk.CTkLabel(tab, text="0 files selected.", font=("Inter", 12))
        self.rename_files_count_label.pack(pady=(0, 10), padx=20, anchor="w")

        # Buttons for selection
        button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        button_frame.pack(pady=(5, 20))

        self.rename_select_files_button = ctk.CTkButton(button_frame, text="Select Files", command=self._select_rename_files, corner_radius=8, width=150, font=("Inter", 13))
        self.rename_select_files_button.grid(row=0, column=0, padx=15)

        self.rename_select_folder_button = ctk.CTkButton(button_frame, text="Select Folder", command=self._select_rename_folder, corner_radius=8, width=150, font=("Inter", 13))
        self.rename_select_folder_button.grid(row=0, column=1, padx=15)

        # New Name Input Section
        ctk.CTkLabel(tab, text="Enter the new base name for the files:", font=("Inter", 13)).pack(pady=(10, 5), padx=20, fill="x")
        self.new_name_entry = ctk.CTkEntry(tab, placeholder_text="E.g. MyPhotos", corner_radius=8, height=38, font=("Inter", 13))
        self.new_name_entry.pack(pady=(0, 10), padx=20, fill="x", expand=True)

        # Sorting Option
        ctk.CTkLabel(tab, text="Sorting Options:", font=("Inter", 13)).pack(pady=(10, 5), padx=20, anchor="w")
        self.sort_options = ["Alphabetically", "Creation Date", "Date Taken (EXIF)"]
        self.sort_option_menu = ctk.CTkOptionMenu(tab, values=self.sort_options, font=("Inter", 13))
        self.sort_option_menu.set("Alphabetically")
        self.sort_option_menu.pack(pady=(0, 10), padx=20, anchor="w")

        # New: Combined Process Checkbox
        self.combine_process_checkbox = ctk.CTkCheckBox(tab, text="Combine processes: Rename and convert RAW to JPG", font=("Inter", 13))
        self.combine_process_checkbox.pack(pady=(10, 5), padx=20, anchor="w")
        ctk.CTkLabel(tab, text="If checked, the selected RAW files will first be renamed according to the options above, and then converted to JPG in the 'exported_jpg' subfolder.", wraplength=550, font=("Inter", 11)).pack(pady=(0, 20), padx=20, anchor="w")

        # Rename Button
        self.rename_button = ctk.CTkButton(tab, text="Rename Files", command=self._rename_files_threaded, corner_radius=10, height=50, font=("Inter", 16, "bold"))
        self.rename_button.pack(pady=10)

    def _select_rename_files(self):
        """Opens a dialog to select multiple files for renaming."""
        self.rename_selected_files = filedialog.askopenfilenames(
            title="Select files to rename",
            filetypes=(("All files", "*.*"), ("Photo files", "*.jpg *.jpeg *.png *.arw *.cr2 *.nef *.dng *.orf *.raf *.pef *.rw2 *.srw *.kdc *.dcr *.mrw *.3fr"), ("Text files", "*.txt"))
        )
        if self.rename_selected_files:
            self.rename_selected_folder = ""
            self.rename_path_label.configure(text=f"{len(self.rename_selected_files)} files selected.")
            self.rename_files_count_label.configure(text=f"{len(self.rename_selected_files)} files selected.")
            self.log_message(f"Selected {len(self.rename_selected_files)} files to rename.")
        else:
            self.rename_path_label.configure(text="No files/folder selected.")
            self.rename_files_count_label.configure(text="0 files selected.")
            self.log_message("File selection for renaming canceled.")

    def _select_rename_folder(self):
        """Opens a dialog to select a folder for renaming."""
        folder_path = filedialog.askdirectory(title="Select folder to rename")
        if folder_path:
            self.rename_selected_folder = folder_path
            self.rename_selected_files = []
            self.rename_path_label.configure(text=f"Selected folder: {self.rename_selected_folder}")
            # Count files in the folder for display
            try:
                num_files = sum(1 for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)))
                self.rename_files_count_label.configure(text=f"{num_files} files in folder.")
                self.log_message(f"Selected folder: {self.rename_selected_folder} for renaming. Number of files: {num_files}.")
            except Exception as e:
                self.rename_files_count_label.configure(text="Error reading file count.")
                self.log_message(f"Error reading file count in folder: {e}.")
        else:
            self.rename_path_label.configure(text="No files/folder selected.")
            self.rename_files_count_label.configure(text="0 files selected.")
            self.log_message("Folder selection for renaming canceled.")

    def _get_exif_date(self, filepath):
        """Extracts the 'DateTimeOriginal' from a file's EXIF data."""
        try:
            with open(filepath, 'rb') as f:
                tags = exifread.process_file(f, stop_tag='DateTimeOriginal')
                if 'EXIF DateTimeOriginal' in tags:
                    date_str = str(tags['EXIF DateTimeOriginal'])
                    return datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                elif 'EXIF DateTimeDigitized' in tags:
                    date_str = str(tags['EXIF DateTimeDigitized'])
                    return datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        except Exception:
            pass
        return None

    def _rename_files_task(self, files_to_rename, new_base_name, sort_method, is_part_of_combined_process=False):
        """The actual file renaming logic, run in a separate thread."""
        if not files_to_rename:
            self.log_message("No files to rename.")
            if not is_part_of_combined_process:
                self.master.after(0, lambda: messagebox.showinfo("Information", "No files to rename in the selected location."))
            return (0, 0, "no_files", []) # Return status for combined process

        # The last_operation_folder is set here for the rename part.
        # For combined process, it will be overwritten by the JPG export folder.
        current_operation_folder = os.path.dirname(files_to_rename[0]) if files_to_rename else ""
        if not is_part_of_combined_process:
            self.last_operation_folder = current_operation_folder

        if sort_method == "Date Taken (EXIF)":
            self.log_message("Sorting files by date taken (EXIF)...")
            files_with_dates = []
            for f_path in files_to_rename:
                exif_date = self._get_exif_date(f_path)
                if exif_date:
                    files_with_dates.append((exif_date, f_path))
                else:
                    try:
                        creation_time = os.path.getctime(f_path)
                        files_with_dates.append((datetime.datetime.fromtimestamp(creation_time), f_path))
                        self.log_message(f"No EXIF date for '{os.path.basename(f_path)}', using creation date.")
                    except OSError:
                        files_with_dates.append((datetime.datetime.min, f_path))
                        self.log_message(f"No EXIF date and error reading creation date for '{os.path.basename(f_path)}'.")

            files_with_dates.sort(key=lambda x: (x[0], x[1]))
            files_to_rename = [f_path for date, f_path in files_with_dates]
            self.log_message("Files sorted by date taken (EXIF).")

        elif sort_method == "Creation Date":
            try:
                files_to_rename.sort(key=lambda f: os.path.getctime(f))
                self.log_message("Files sorted by creation date.")
            except OSError as e:
                self.log_message(f"Error while sorting files by creation date: {e}. Continuing with alphabetical sort.")
                files_to_rename.sort()
        else: # "Alphabetically"
            files_to_rename.sort()
            self.log_message("Files sorted alphabetically.")

        total_files = len(files_to_rename)
        num_digits = max(2, len(str(total_files)))

        self.log_message(f"Starting to rename {total_files} files...")
        renamed_count = 0
        failed_count = 0
        renamed_paths = [] # To return new paths for combined process

        for i, old_path in enumerate(files_to_rename):
            directory, old_filename = os.path.split(old_path)
            _, file_extension = os.path.splitext(old_filename)

            counter = str(i + 1).zfill(num_digits)
            new_filename = f"{new_base_name}_{counter}{file_extension}"
            new_path = os.path.join(directory, new_filename)

            try:
                os.rename(old_path, new_path)
                self.log_message(f"Renamed: '{old_filename}' to '{new_filename}'")
                renamed_count += 1
                renamed_paths.append(new_path)
            except OSError as e:
                self.log_message(f"Error renaming '{old_filename}': {e}")
                failed_count += 1
                renamed_paths.append(old_path) # Keep old path if rename failed
            except Exception as e:
                self.log_message(f"Unexpected error renaming '{old_filename}': {e}")
                failed_count += 1
                renamed_paths.append(old_path) # Keep old path if rename failed

        self.log_message("--- Renaming finished ---")
        self.log_message(f"Successfully renamed {renamed_count} files.")
        if failed_count > 0:
            self.log_message(f"Failed to rename {failed_count} files.")
        
        return (renamed_count, failed_count, "completed", renamed_paths)


    def _rename_files_threaded(self):
        """Starts the file renaming process in a new thread."""
        new_base_name = self.new_name_entry.get().strip()
        if not new_base_name:
            messagebox.showerror("Error", "Please enter a new base name.")
            self.log_message("Error: No base name entered.")
            return

        files_to_process = []
        if self.rename_selected_files:
            files_to_process = list(self.rename_selected_files)
        elif self.rename_selected_folder:
            try:
                files_to_process = [os.path.join(self.rename_selected_folder, f) for f in os.listdir(self.rename_selected_folder) if os.path.isfile(os.path.join(self.rename_selected_folder, f))]
            except OSError as e:
                messagebox.showerror("Error", f"Could not read folder: {e}")
                self.log_message(f"Error reading folder: {e}")
                return
        else:
            messagebox.showwarning("Warning", "Please select files or a folder.")
            self.log_message("Warning: No files or folder selected.")
            return

        if not files_to_process:
            messagebox.showinfo("Information", "No files to rename in the selected location.")
            self.log_message("No files to rename.")
            return
        
        # Disable button during operation
        self.rename_button.configure(state="disabled")
        self.log_message("Starting background operation...")

        sort_method = self.sort_option_menu.get()
        combined_process = self.combine_process_checkbox.get() == 1

        # Start a new thread for the combined or rename-only task
        processing_thread = threading.Thread(target=self._run_combined_or_rename_task, args=(files_to_process, new_base_name, sort_method, combined_process))
        processing_thread.start()

    def _run_combined_or_rename_task(self, files_to_process, new_base_name, sort_method, combined_process):
        """Handles either renaming only or combined rename+convert."""
        renamed_count, rename_failed_count, rename_status_str, renamed_paths = \
            self._rename_files_task(files_to_process, new_base_name, sort_method, is_part_of_combined_process=combined_process)

        if rename_status_str == "no_files":
            self.master.after(0, lambda: self.rename_button.configure(state="normal"))
            return

        if combined_process:
            self.log_message("\n--- Starting combined process: Rename RAW + Convert to JPG ---")
            
            # Filter for RAW files among the renamed paths for conversion
            raw_files_for_conversion = [f_path for f_path in renamed_paths if f_path.lower().endswith(self.supported_raw_formats)]

            if not raw_files_for_conversion:
                self.log_message("No RAW files to convert after renaming. Ending combined process.")
                self.master.after(0, lambda: messagebox.showinfo("Information", "No RAW files to convert after renaming."))
                self.master.after(0, lambda: self.rename_button.configure(state="normal"))
                return

            self.log_message("\nStep 2/2: Converting newly named RAW files to JPG...")
            
            # The base directory for JPG export will be the directory of the first renamed file
            output_dir_base = os.path.dirname(raw_files_for_conversion[0])
            processed_count, skipped_count, failed_count = self._perform_raw_conversion_task(raw_files_for_conversion, output_dir_base)

            self.last_operation_folder = os.path.join(output_dir_base, 'exported_jpg') # Update folder for combined process

            final_msg_title = "Combined Process Finished"
            final_msg = f"Renaming: {renamed_count} successful, {rename_failed_count} failed.\n" \
                        f"RAW to JPG Conversion: {processed_count} processed, {skipped_count} skipped, {failed_count} failed."
            
            if rename_failed_count > 0 or failed_count > 0:
                final_msg_title = "Combined Process Finished with Errors"
                
            self.master.after(0, lambda: self._show_completion_dialog(final_msg_title, final_msg, self.last_operation_folder))

        else: # Only rename
            self.master.after(0, lambda: self.rename_button.configure(state="normal")) # Re-enable button
            msg = f"Successfully renamed {renamed_count} files."
            if rename_failed_count > 0:
                msg += f"\nFailed to rename {rename_failed_count} files."
                self.master.after(0, lambda: self._show_completion_dialog("Finished with Errors", msg, self.last_operation_folder))
            else:
                self.master.after(0, lambda: self._show_completion_dialog("Finished", msg, self.last_operation_folder))
        
        self.master.after(0, lambda: self.rename_button.configure(state="normal")) # Ensure button is re-enabled


    # --- UI for "Convert RAW to JPG" Tab ---
    def _create_raw_to_jpg_tab_ui(self, tab):
        ctk.CTkLabel(tab, text="Convert RAW files (.ARW, .CR2, etc.) to JPG.", wraplength=550, font=("Inter", 14, "bold")).pack(pady=(15, 5), padx=20, fill="x")
        ctk.CTkLabel(tab, text="JPG files will be rotated based on EXIF data and saved in the 'exported_jpg' subfolder.", wraplength=550, font=("Inter", 12)).pack(pady=(0, 15), padx=20, fill="x")

        self.raw_folder_label = ctk.CTkLabel(tab, text="No RAW folder selected.", wraplength=550, font=("Inter", 12))
        self.raw_folder_label.pack(pady=5, padx=20, fill="x")

        self.select_raw_folder_button = ctk.CTkButton(tab, text="Select Folder with RAW Files", command=self._select_raw_folder_for_conversion, corner_radius=8, width=200, font=("Inter", 13))
        self.select_raw_folder_button.pack(pady=10)

        ctk.CTkLabel(tab, text="Use the 'Rename Files' tab to combine renaming with RAW to JPG conversion.", wraplength=550, font=("Inter", 11, "italic")).pack(pady=(10, 20), padx=20, anchor="w")

        self.start_raw_conversion_button = ctk.CTkButton(tab, text="Start Conversion (RAW to JPG only)", command=self._start_raw_conversion_threaded, corner_radius=10, height=50, font=("Inter", 16, "bold"), state="disabled")
        self.start_raw_conversion_button.pack(pady=20)

    def _select_raw_folder_for_conversion(self):
        """Opens a dialog to select a folder containing RAW files for conversion."""
        folder_path = filedialog.askdirectory(title="Select folder with RAW files")
        if folder_path:
            self.raw_conversion_folder = folder_path
            self.raw_folder_label.configure(text=f"Selected RAW folder: {self.raw_conversion_folder}")
            self.log_message(f"Selected RAW folder for conversion: {self.raw_conversion_folder}")
            self.start_raw_conversion_button.configure(state="normal") # Enable button
        else:
            self.raw_folder_label.configure(text="No RAW folder selected.")
            self.log_message("RAW folder selection canceled.")
            self.start_raw_conversion_button.configure(state="disabled") # Disable button

    def _rotate_image_based_on_exif(self, image):
        """Rotates a PIL Image object based on its EXIF Orientation tag."""
        try:
            exif = image.getexif()
            if exif:
                orientation_tag_id = 274 # Hex 0x0112, corresponds to Orientation
                if orientation_tag_id in exif:
                    orientation = exif[orientation_tag_id]
                    if orientation == 3:
                        image = image.rotate(180, expand=True)
                    elif orientation == 6:
                        image = image.rotate(270, expand=True)
                    elif orientation == 8:
                        image = image.rotate(90, expand=True)
        except Exception as e:
            self.log_message(f"Warning: Error processing EXIF data for rotation: {e}")
        return image

    def _process_single_raw_image(self, raw_file_path, output_file):
        """Processes a single RAW file, extracts the thumbnail, rotates it, and saves as JPG."""
        try:
            with rawpy.imread(raw_file_path) as raw:
                # Extract the embedded thumbnail, which is usually a JPG
                embedded_image = raw.extract_thumb()
                if embedded_image.format == rawpy.ThumbFormat.JPEG:
                    img = Image.open(io.BytesIO(embedded_image.data))
                    img = self._rotate_image_based_on_exif(img)
                    img.save(output_file, "jpeg", quality=95, optimize=True)
                    self.log_message(f"Saved and rotated JPG preview: '{os.path.basename(output_file)}'")
                    return True
                else:
                    self.log_message(f"Warning: Embedded JPG image not found in RAW file: '{os.path.basename(raw_file_path)}'")
                    return False
        except rawpy.LibRawFileException as e:
            self.log_message(f"LibRaw error while processing '{os.path.basename(raw_file_path)}': {e}")
            return False
        except Exception as e:
            self.log_message(f"Unexpected error while processing '{os.path.basename(raw_file_path)}': {e}")
            return False

    def _start_raw_conversion_threaded(self):
        """Starts the RAW to JPG conversion process in a new thread."""
        if not self.raw_conversion_folder or not os.path.isdir(self.raw_conversion_folder):
            messagebox.showerror("Error", "Please select a valid RAW folder.")
            self.log_message("Error: No valid RAW folder selected.")
            return

        self.start_raw_conversion_button.configure(state="disabled")
        self.log_message("Starting RAW to JPG conversion in the background...")

        conversion_thread = threading.Thread(target=self._run_raw_conversion_task)
        conversion_thread.start()

    def _run_raw_conversion_task(self):
        """The actual RAW to JPG conversion logic, run in a separate thread."""
        raws_dir = self.raw_conversion_folder
        
        files_to_process_for_conversion = [os.path.join(raws_dir, f) for f in os.listdir(raws_dir) if os.path.isfile(os.path.join(raws_dir, f)) and f.lower().endswith(self.supported_raw_formats)]
        self.log_message(f"Starting standard RAW to JPG conversion in '{raws_dir}'...")

        processed_count, skipped_count, failed_count = self._perform_raw_conversion_task(files_to_process_for_conversion, raws_dir)

        self.last_operation_folder = os.path.join(raws_dir, 'exported_jpg') # Update last operation folder

        # Show final message box on the main thread
        if failed_count > 0:
            self.master.after(0, lambda: self._show_completion_dialog("Finished with Errors", f"Conversion finished with {failed_count} errors.", self.last_operation_folder))
        else:
            self.master.after(0, lambda: self._show_completion_dialog("Finished", "All RAW files were processed successfully.", self.last_operation_folder))

        self.master.after(0, lambda: self.start_raw_conversion_button.configure(state="normal")) # Re-enable button


    def _perform_raw_conversion_task(self, files_to_convert, output_dir_base):
        """Core logic for RAW to JPG conversion, can be called by combined process or direct conversion."""
        processed_count = 0
        skipped_count = 0
        failed_count = 0
        final_jpg_folder = os.path.join(output_dir_base, 'exported_jpg')

        if not os.path.exists(final_jpg_folder):
            os.makedirs(final_jpg_folder)
            self.log_message(f"Created JPG output folder: {final_jpg_folder}")
        
        if not files_to_convert:
            self.log_message("No RAW files to process.")
            return (0, 0, 0) # Return counts

        for raw_file_path in files_to_convert:
            filename = os.path.basename(raw_file_path)
            output_file = os.path.join(final_jpg_folder, os.path.splitext(filename)[0] + '.jpg')

            if os.path.exists(output_file):
                self.log_message(f"Skipping '{os.path.basename(output_file)}' (already exists).")
                skipped_count += 1
            else:
                if self._process_single_raw_image(raw_file_path, output_file):
                    processed_count += 1
                else:
                    failed_count += 1
        
        return (processed_count, skipped_count, failed_count)


    # Expanded list of common RAW formats (class attribute)
    supported_raw_formats = (
        '.arw', '.cr2', '.cr3', '.nef', '.dng', '.orf', '.raf', '.pef',
        '.rw2', '.srw', '.kdc', '.dcr', '.mrw', '.3fr'
    )

    def _show_completion_dialog(self, title, message, folder_path=None):
        """Shows a custom completion dialog with an 'Open Folder' button."""
        dialog = ctk.CTkToplevel(self.master)
        dialog.title(title)
        dialog.geometry("380x200") # Increased size for better readability
        dialog.transient(self.master) # Make it appear on top of the main window
        dialog.grab_set() # Make it modal

        ctk.CTkLabel(dialog, text=message, wraplength=340, justify="center", font=("Inter", 13)).pack(pady=15)
        
        if folder_path and os.path.exists(folder_path):
            open_folder_btn = ctk.CTkButton(dialog, text="Open Folder", command=lambda: [self._open_folder_in_explorer(folder_path), dialog.destroy()], font=("Inter", 13))
            open_folder_btn.pack(pady=5)
        
        close_btn = ctk.CTkButton(dialog, text="Close", command=dialog.destroy, font=("Inter", 13))
        close_btn.pack(pady=5)

        self.master.wait_window(dialog) # Wait for dialog to close


if __name__ == "__main__":
    root = ctk.CTk()
    app = FileToolApp(root)
    root.mainloop()
