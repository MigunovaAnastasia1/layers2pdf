#!/bin/bash
# install.sh - Linux installation script file Krita Layers2PDF plugin

echo "📁 Installing Krita Layers2PDF plugin..."

# Krita pykrita path
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    KRITA_PYKRITA="$HOME/.local/share/krita/pykrita"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    KRITA_PYKRITA="~/Library/Application Support/Krita/pykrita"
else
    # Unsupported OS
    echo "❌ ERROR: Unsupported operating system"
    exit 1
fi

# Create folder if it doesn't exist
mkdir -p "$KRITA_PYKRITA"


# Copy plugin folder
if [ -d "layers2pdf" ]; then
    cp -r layers2pdf "$KRITA_PYKRITA/"

    if [ ! -d "$KRITA_PYKRITA/layers2pdf" ]; then
    	echo "❌ ERROR: Failed to copy 'layers2pdf' folder to $KRITA_PYKRITA"
    	echo "   Check permissions and disk space."
    	exit 1
    fi
    echo "   ✅ Plugin folder copied"
else
    echo "❌ ERROR: 'layers2pdf' folder not found!"
    echo "   Make sure you run this script from the repository root."
    exit 1
fi


# Copy .desktop file to the same location
if [ -f "layers2pdf.desktop" ]; then
    cp layers2pdf.desktop "$KRITA_PYKRITA/"
    
    if [ ! -f "$KRITA_PYKRITA/layers2pdf.desktop" ]; then
        echo "❌ ERROR: Failed to copy 'layers2pdf.desktop' to $KRITA_PYKRITA"
        echo "   Check permissions and disk space."
        exit 1
    fi
    echo "   ✅ Desktop file copied"
else
    echo "❌ ERROR: 'layers2pdf.desktop' file not found!"
    echo "   Make sure you run this script from the repository root."
    exit 1
fi

echo ""
echo "✅ Plugin installed successfully!"
echo ""
echo "📌 Next steps:"
echo "   1. Restart Krita"
echo "   2. Go to Settings → Configure Krita → Python Plugin Manager"
echo "   3. Enable 'Export Layers to PDF' plugin"
echo "   4. Restart Krita again"
