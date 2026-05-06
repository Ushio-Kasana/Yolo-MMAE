#!/bin/bash
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