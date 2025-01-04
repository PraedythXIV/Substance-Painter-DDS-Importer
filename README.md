# Substance-Painter-DDS-Importer

A Substance Painter plugin for importing DDS files. It converts DDS to PNG, extracts alpha channels, and imports them to the shelf under session resources. Optionally, it decodes BC5_SNORM textures and reconstructs the Z channel.

![banner](https://staticdelivery.nexusmods.com/mods/2295/images/1044/1044-1726769824-1173798291.png)

- This plugin helps users easily import DDS textures to their shelf as session resources by converting them to PNGs. It also extracts alpha channels and imports them as separate resources.
- If needed, it can decode and reconstruct the Z channel of BC5 DDS textures. This feature is particularly useful for Fallout 4, Fallout 76, and Starfield normal maps. Once processed, these textures are also imported as session resources.

**Requirements:**
- [DirectXTex for TexConv](https://github.com/microsoft/DirectXTex)
- [Fo76Utils for BcDecode](https://github.com/fo76utils/fo76utils)
- [Pillow](https://pypi.org/project/pillow/)

**Installation:**
1. Download the plugin files and place them in your Substance Painter `plugins` folder:
   - Windows: `%userprofile%\Documents\Substance Painter\plugins`
   - macOS: `~/Library/Application Support/Allegorithmic/Substance Painter/plugins`

2. Ensure the required tools (TexConv and BcDecode) are installed and accessible.

3. Install **Pillow**:
   - Open the Command Prompt.
   - Run the following command to install Pillow for the Substance Painter Python environment:
     ```bash
     "C:\Program Files\Adobe\Adobe Substance 3D Painter\resources\pythonsdk\python.exe" -m pip install Pillow
     ```
   - Verify the installation by running:
     ```bash
     "C:\Program Files\Adobe\Adobe Substance 3D Painter\resources\pythonsdk\python.exe" -m pip show Pillow
     ```

4. Start Substance Painter. The plugin should load automatically.

**Usage:**
1. Open the plugin from the Substance Painter `Plugins` menu.
2. Use the "Set texconv Location" and "Set bcdecode Location" buttons to configure the paths to TexConv and BcDecode executables.
3. Click "Import" to convert DDS files to PNG and import them to the shelf.
4. For BC5_SNORM textures, use the "Decode and Reconstruct" option to process and import them.
