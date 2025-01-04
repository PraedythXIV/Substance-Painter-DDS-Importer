__author__ = "Yohan ROBERT"
__copyright__ = "Copyright 2025, Yohan ROBERT"
__version__ = "1.0.4"
__painterVersion__ = "10.1.2"

import os
import subprocess
import traceback
import configparser
from PIL import Image, UnidentifiedImageError

import substance_painter as sp
from substance_painter.resource import Usage

# Check for the Substance Painter version to determine the correct PySide version
IsQt5 = sp.application.version_info() < (10, 1, 0)

if IsQt5:
    from PySide2 import QtWidgets
    from PySide2.QtCore import Qt
else:
    from PySide6 import QtWidgets
    from PySide6.QtCore import Qt

import substance_painter.ui

# Utility Functions

def show_message_box(title, text):
    """
    Display a message box with the specified title and text.

    :param title: Title of the message box
    :param text: Text content of the message box
    """
    msg = QtWidgets.QMessageBox()
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.exec_()

def log_to_painter_console(message):
    """Log a message to the Substance Painter console."""
    print(message)

def run_bcdecode(bcdecode_exe, input_dds, output_dds):
    """
    Run the bcdecode tool to decode a BC5_SNORM DDS file into an uncompressed DDS file.

    :param bcdecode_exe: Path to the bcdecode executable
    :param input_dds: Path to the input BC5_SNORM DDS file
    :param output_dds: Path to the output uncompressed DDS file
    :raises RuntimeError: If the bcdecode command fails
    """
    cmd = [
        bcdecode_exe,
        input_dds,
        output_dds,
        "0",  # Specify face=0
        "2"   # Reconstruct normal map Z
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"bcdecode failed with code {result.returncode}\n{result.stderr}")

def convert_dds_to_png(texconv_exe, dds_file, output_png):
    """
    Convert a DDS file to PNG using texconv.

    :param texconv_exe: Path to the texconv executable
    :param dds_file: Path to the input DDS file
    :param output_png: Path to the output PNG file
    :raises RuntimeError: If the texconv command fails
    """
    try:
        command = [
            texconv_exe,
            "-ft", "png",  # Output format
            "-o", os.path.dirname(output_png),  # Output directory
            "-y",  # Overwrite existing files
            dds_file  # Input DDS file
        ]
        print(f"Running texconv command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"texconv failed with code {result.returncode}:\n{result.stderr.strip()}\n{result.stdout.strip()}")

    except Exception as e:
        raise RuntimeError(f"Failed to convert {dds_file} to PNG: {e}")

def extract_alpha_channel(input_png, output_alpha_png):
    """
    Extract the alpha channel from a PNG file and save it as a separate PNG.
    Returns True if an alpha channel was found and extracted, False otherwise.

    :param input_png: Path to the input PNG file
    :param output_alpha_png: Path to the output alpha PNG file
    :return: Boolean indicating if alpha was extracted
    :raises RuntimeError: If extraction fails
    """
    try:
        with Image.open(input_png) as img:
            if img.mode in ("RGBA", "LA") or ("A" in img.getbands()):
                alpha = img.getchannel("A")
                alpha.save(output_alpha_png)
                return True
            return False
    except UnidentifiedImageError as e:
        raise RuntimeError(f"Failed to extract alpha channel from {input_png}: {e}")

def remove_alpha_channel(input_png):
    """
    Remove the alpha channel from a PNG file.

    :param input_png: Path to the input PNG file
    :raises RuntimeError: If removal fails
    """
    try:
        with Image.open(input_png) as img:
            if img.mode == "RGBA":
                rgb_image = img.convert("RGB")
                rgb_image.save(input_png)
    except UnidentifiedImageError as e:
        raise RuntimeError(f"Failed to remove alpha channel from {input_png}: {e}")

# Main Plugin Class

class DDSImporterPlugin:
    """
    A plugin to handle importing DDS files and BC5_SNORM DDS files into Substance Painter.
    Converts DDS textures to PNG using texconv and handles BC5_SNORM using bcdecode.
    """
    CONFIG_FILE = os.path.join(os.path.dirname(__file__), "DDS-Importer.ini")

    def __init__(self):
        # Create the main plugin window
        self.window = QtWidgets.QWidget()
        self.window.setWindowTitle("DDS Importer")

        # Set up the layout and buttons
        layout = QtWidgets.QVBoxLayout(self.window)

        # Log window
        self.log_window = QtWidgets.QTextEdit()
        self.log_window.setReadOnly(True)
        layout.addWidget(self.log_window)

        # DDS Section
        self.dds_group = QtWidgets.QGroupBox("Import DDS files to session resources as png")
        dds_layout = QtWidgets.QVBoxLayout()
        self.import_dds_btn = QtWidgets.QPushButton("Import")
        dds_layout.addWidget(self.import_dds_btn)
        self.dds_group.setLayout(dds_layout)
        layout.addWidget(self.dds_group)

        # BC5_SNORM Section
        self.bc5_group = QtWidgets.QGroupBox("Decode and reconstruct Z channel of BC5 dds then import")
        bc5_layout = QtWidgets.QVBoxLayout()
        self.import_bc5_btn = QtWidgets.QPushButton("Decode and reconstruct")
        bc5_layout.addWidget(self.import_bc5_btn)
        self.bc5_group.setLayout(bc5_layout)
        layout.addWidget(self.bc5_group)

        # Configuration and Log Controls
        self.config_group = QtWidgets.QGroupBox("Configuration & Logs")
        config_layout = QtWidgets.QHBoxLayout()

        # Buttons
        self.set_texconv_btn = QtWidgets.QPushButton("Set texconv Location")
        self.set_bcdecode_btn = QtWidgets.QPushButton("Set bcdecode Location")
        self.toggle_log_btn = QtWidgets.QPushButton("Show/Hide Log")
        self.clear_log_btn = QtWidgets.QPushButton("Clear Log")

        # Add buttons to layout
        config_layout.addWidget(self.set_texconv_btn)
        config_layout.addWidget(self.set_bcdecode_btn)
        config_layout.addWidget(self.toggle_log_btn)
        config_layout.addWidget(self.clear_log_btn)

        self.config_group.setLayout(config_layout)
        layout.addWidget(self.config_group)

        # Connect buttons to handlers
        self.import_dds_btn.clicked.connect(self.on_import_dds)
        self.import_bc5_btn.clicked.connect(self.on_import_bc5)
        self.set_texconv_btn.clicked.connect(self.set_texconv_location)
        self.set_bcdecode_btn.clicked.connect(self.set_bcdecode_location)
        self.toggle_log_btn.clicked.connect(self.toggle_log_visibility)
        self.clear_log_btn.clicked.connect(self.clear_log)

        # Add the plugin window as a dockable widget in Substance Painter
        substance_painter.ui.add_dock_widget(self.window)

        # Load configuration
        self.config = configparser.ConfigParser()
        self.load_config()

        # Display initial information
        self.display_initial_info()

        # Check for Pillow
        self.check_pillow_installation()

    def check_pillow_installation(self):
        try:
            import PIL
            self.log("Pillow installed: Yes")
        except ImportError:
            self.log("Pillow installed: No")
            self.log("To install Pillow:")
            self.log("1. Open the Windows Command Prompt (type 'cmd' in the Windows search bar and press Enter).")
            self.log("2. Copy and paste the following command, then press Enter:")
            self.log("\"C:\\Program Files\\Adobe\\Adobe Substance 3D Painter\\resources\\pythonsdk\\python.exe\" -m pip install Pillow")

    def display_initial_info(self):
        texconv_path = self.config["Paths"].get("texconv", "Not set")
        bcdecode_path = self.config["Paths"].get("bcdecode", "Not set")
        self.log(f"texconv location: {texconv_path}")
        self.log(f"bcdecode location: {bcdecode_path}")

    def log(self, message):
        """Log a message to the log window and console."""
        self.log_window.append(message)
        log_to_painter_console(message)

    def toggle_log_visibility(self):
        """Toggle the visibility of the log window."""
        self.log_window.setVisible(not self.log_window.isVisible())

    def clear_log(self):
        """Clear the log window."""
        self.log_window.clear()

    def load_config(self):
        """Load configuration from the ini file, or create it if it doesn't exist."""
        if not os.path.exists(self.CONFIG_FILE):
            self.create_default_config()
        self.config.read(self.CONFIG_FILE)

    def create_default_config(self):
        """Create a default configuration file."""
        self.config["Paths"] = {
            "texconv": r"C:\\DirectXTex\\Texconv\\texconv.exe",
            "bcdecode": r"C:\\fo76utils\\bcdecode.exe"
        }
        self.save_config()

    def save_config(self):
        """Save the configuration to the ini file."""
        try:
            with open(self.CONFIG_FILE, 'w') as configfile:
                self.config.write(configfile)
        except IOError as e:
            self.log(f"Failed to save configuration: {e}")

    def set_texconv_location(self):
        """Allow the user to set the location of the texconv executable."""
        texconv_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self.window,
            caption="Select texconv Executable",
            filter="Executables (*.exe);;All Files (*.*)"
        )
        if texconv_path:
            self.config["Paths"]["texconv"] = texconv_path
            self.save_config()
            self.log(f"texconv location set to: {texconv_path}")
        else:
            self.log("Texconv executable not set. Get the latest version here: https://github.com/microsoft/DirectXTex")

    def set_bcdecode_location(self):
        """Allow the user to set the location of the bcdecode executable."""
        bcdecode_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self.window,
            caption="Select bcdecode Executable",
            filter="Executables (*.exe);;All Files (*.*)"
        )
        if bcdecode_path:
            self.config["Paths"]["bcdecode"] = bcdecode_path
            self.save_config()
            self.log(f"bcdecode location set to: {bcdecode_path}")
        else:
            self.log("bcdecode executable not set. Please ensure bcdecode is installed.")

    def on_import_dds(self):
        """
        Handle the import DDS button click event to convert DDS textures to PNG.
        """
        # Open file dialog to select DDS files
        dds_files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            parent=self.window,
            caption="Select DDS Files to Import",
            filter="DDS Files (*.dds);;All Files (*.*)"
        )
        if not dds_files:
            self.log("No DDS files selected for import.")
            return

        texconv_exe = self.config["Paths"].get("texconv", None)

        # Check if texconv is valid
        if not texconv_exe or not os.path.isfile(texconv_exe):
            self.log("Invalid or missing texconv executable. Please set it using the 'Set texconv Location' button.")
            return

        for dds_file in dds_files:
            try:
                output_png = os.path.splitext(dds_file)[0] + ".png"
                output_alpha_png = os.path.splitext(dds_file)[0] + "_alpha.png"

                # Convert directly to PNG via texconv
                self.log(f"Converting {dds_file} to PNG directly using texconv...")
                convert_dds_to_png(texconv_exe, dds_file, output_png)

                # Extract alpha channel if present
                if extract_alpha_channel(output_png, output_alpha_png):
                    remove_alpha_channel(output_png)
                    self.log(f"Alpha channel extracted to: {output_alpha_png}")
                else:
                    self.log(f"No alpha channel found in: {dds_file}")

                # Import the PNG(s) into the Substance Painter shelf
                self.log(f"Converted to: {output_png}")
                self.import_to_shelf(output_png)
                if os.path.exists(output_alpha_png):
                    self.import_to_shelf(output_alpha_png)

            except Exception as e:
                self.log(f"Failed to process {dds_file}: {e}")
                traceback.print_exc()

    def on_import_bc5(self):
        """
        Handle the import BC5_SNORM button click event to run the bcdecode process.
        """
        # Open a file dialog to select the input BC5_SNORM DDS file
        bc5_input = QtWidgets.QFileDialog.getOpenFileName(
            parent=self.window,
            caption="Select BC5_SNORM DDS (input)",
            filter="DDS Files (*.dds);;All Files (*.*)"
        )[0]
        if not bc5_input:
            show_message_box("Cancelled", "No BC5_SNORM input file selected.")
            return

        # Open a file dialog to specify the output uncompressed DDS file
        out_dds = QtWidgets.QFileDialog.getSaveFileName(
            parent=self.window,
            caption="Save Uncompressed DDS (output)",
            filter="DDS Files (*.dds);;All Files (*.*)"
        )[0]
        if not out_dds:
            show_message_box("Cancelled", "No output DDS file selected.")
            return

        # Determine the path to the bcdecode executable
        bcdecode_exe = self.config["Paths"].get("bcdecode", None)
        if not bcdecode_exe or not os.path.isfile(bcdecode_exe):
            self.log("Invalid or missing bcdecode executable. Please set it using the 'Set bcdecode Location' button.")
            return

        try:
            # Run the bcdecode process
            self.log(f"Running bcdecode on {bc5_input}...")
            run_bcdecode(bcdecode_exe, bc5_input, out_dds)
            self.log(f"bcdecode successful:\n{os.path.basename(bc5_input)} -> {out_dds}")
            show_message_box("Import Successful", f"bcdecode => {os.path.basename(bc5_input)}\n-> {out_dds}")

            # Optionally, import the decoded DDS into the shelf
            self.import_to_shelf(out_dds)

        except Exception as e:
            traceback.print_exc()
            self.log(f"Error importing BC5_SNORM DDS: {e}")
            show_message_box("Error Importing BC5_SNORM DDS", str(e))

    def import_to_shelf(self, resource_path):
        """
        Import the given resource as a session resource into the Substance Painter shelf.

        :param resource_path: Path to the resource file to import
        """
        try:
            sp.resource.import_session_resource(
                file_path=resource_path,
                resource_usage=Usage.TEXTURE,
                name=os.path.basename(resource_path)
            )
            self.log(f"Imported to shelf: {resource_path}")
        except Exception as e:
            self.log(f"Failed to import {resource_path} to shelf: {e}")

    def __del__(self):
        """
        Clean up by removing the UI elements when the plugin is destroyed.
        """
        substance_painter.ui.delete_ui_element(self.window)

# Plugin Lifecycle

PLUGIN_INSTANCE = None

def start_plugin():
    """
    Initialize and start the plugin.
    """
    global PLUGIN_INSTANCE
    PLUGIN_INSTANCE = DDSImporterPlugin()

def close_plugin():
    """
    Clean up and stop the plugin.
    """
    global PLUGIN_INSTANCE
    del PLUGIN_INSTANCE
