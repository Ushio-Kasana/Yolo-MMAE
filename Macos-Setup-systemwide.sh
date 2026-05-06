#!/bin/bash
# YOLO-MMAE - Video Annotator & Auto-Tracker
# Copyright (C) 2026  Ushio-Kasana
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#Check if Brew is installed
echo "Checking if homebrew is currently installed"
if command -v brew &>/dev/null; then
    echo "✅ Homebrew is installed"
    echo "Trying to install python3.10 via Brew"
    if brew install python@3.10; then
        echo "python3.10 has been installed via Brew"
    else
        read -p "Failed to install python3.10, would you like me to try again? (y/n): " replyp
        if [[ "$replyp" == "y" || "$replyp" == "Y" ]]; then
            echo "Trying to install python again"
            if brew install python@3.10; then
                echo "python3.10 has been installed via Brew"
            else
                echo "Failed to install"
                exit 1
            fi
        else
            exit 1
        fi
    fi
    cd src
    if python3.10 -m pip install -r requirements.txt; then
        echo "Python Requirements Installed"
    else
        read -p "Failed to install Requirements, would you like to try again? (y/n): " reply2
        if [[ "$reply2" == "y" || "$reply2" == "Y" ]]; then
            echo "Trying again"
            if python3.10 -m pip install -r requirements.txt; then
                echo "Python Requirements Installed"
            else
                echo "Failed to install Requirements"
                exit 1
            fi
        fi
    fi
else
    echo "❌ Homebrew is not installed."
    read -p "Would you like to install it now? (y/n): " reply
    if [[ "$reply" == "y" || "$reply" == "Y" ]]; then
        echo "Installing Homebrew now"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        eval "$(/opt/homebrew/bin/brew shellenv)"
        if command -v brew &>/dev/null; then
            echo "✅ Homebrew is now installed"
            echo "Trying to install python3.10 via Brew"
            if brew install python@3.10; then
                echo "python3.10 has been installed via Brew"
            else
                read -p "Failed to install python3.10, would you like me to try again? (y/n): " replyp
                if [[ "$replyp" == "y" || "$replyp" == "Y" ]]; then
                    echo "Trying to install python again"
                    if brew install python@3.10; then
                        echo "python3.10 has been installed via Brew"
                    else
                        echo "Failed to install"
                        exit 1
                    fi
                else
                    exit 1
                fi
            fi
            cd src
            if python3.10 -m pip install -r requirements.txt; then
                echo "Python Requirements Installed"
            else
                read -p "Failed to install Requirements, would you like to try again? (y/n): " reply2
                if [[ "$reply2" == "y" || "$reply2" == "Y" ]]; then
                    echo "Trying again"
                    if python3.10 -m pip install -r requirements.txt; then
                        echo "Python Requirements Installed"
                    else
                        echo "Failed to install Requirements"
                        exit 1
                    fi
                fi
            fi
        else
            echo "Homebrew failed to install, please make sure you have access to an active network connection and try again."
        fi
    else
        echo "If I can't install Brew then I would either recommend running the Macos-Setup-Venv.sh script instead or running the main.py script in src and installing the imports and tools yourself."
    fi
fi