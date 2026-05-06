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
#check if python is installed
if command -v python3.10 &>/dev/null; then
    echo "Python 3.10 is installed"
else
     if command -v brew &>/dev/null; then
        echo "✅ Homebrew is installed"
        read -p "Python 3.10 is not installed woukd you like to install it via Brew? (y/n): " pythoninstall
        if [[ "$pythoninstall" == "y" || "$pythoninstall" == "Y" ]]; then
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
                    echo "if you would like to manully install this program then follow the instrutions on the github"
                    exit 1
                fi
            fi
        else
            echo "cant install python3.10 neeeded to run script, either look at the other method of instlation or follow the manual "
            exit 1
        fi
    else
        read -p "Brew is not installed would you like me to install Brew (y/n): " brewinstall
        if [[ "$brewinstall" == "y" || "$brewinstall" == "Y" ]]; then
            echo "Installing Homebrew now"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            eval "$(/opt/homebrew/bin/brew shellenv)"
            if command -v brew &>/dev/null; then
                echo "✅ Homebrew is now installed"
                read -p "Python 3.10 is not installed woukd you like to install it via Brew? (y/n): " pythoninstall
                if [[ "$pythoninstall" == "y" || "$pythoninstall" == "Y" ]]; then
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
                            echo "if you would like to manully install this program then follow the instrutions on the github"
                            exit 1
                        fi
                    fi
                else
                    echo "if you would like to manully install this program then follow the instrutions on the github"
                    exit 1
                fi
            else
                echo "Please either restart your terminal session or restart your IDE/Code Editor"
                exit 1
            fi
        else
            echo "if you would like to manully install this program then follow the instrutions on the github"
            exit 1
        fi
    fi
fi
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3.10 -m venv venv
source "$SCRIPT_DIR/venv/bin/activate"
cd src
pip install -r requirements.txt
cd ..
echo "Program has been installed you may now run Macos-Start-Venv.sh"
exit 0