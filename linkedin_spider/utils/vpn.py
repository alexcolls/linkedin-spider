"""VPN management utilities for LinkedIn Spider."""

import subprocess
import time
from typing import Optional

from linkedin_spider.utils.config import config
from linkedin_spider.utils.logger import logger


class VPNManager:
    """Manages VPN connections for IP rotation."""

    def __init__(self, command: Optional[str] = None, enabled: Optional[bool] = None):
        """
        Initialize VPN manager.

        Args:
            command: VPN command to execute. If None, uses config value.
            enabled: Whether VPN switching is enabled. If None, uses config value.
        """
        self.command = command or config.vpn_command
        self.enabled = enabled if enabled is not None else config.vpn_enabled
        self.switch_count = 0
        self.switch_frequency = config.vpn_switch_frequency

    def connect(self) -> bool:
        """
        Connect to VPN.

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("VPN switching is disabled")
            return False

        if not self.command:
            logger.warning("VPN command not configured")
            return False

        try:
            logger.info(f"Connecting to VPN: {self.command}")
            result = subprocess.run(
                self.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                logger.info("VPN connected successfully")
                time.sleep(2)  # Wait for connection to stabilize
                return True
            else:
                logger.error(f"VPN connection failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("VPN connection timed out")
            return False
        except Exception as e:
            logger.error(f"VPN connection error: {e}")
            return False

    def disconnect(self) -> bool:
        """
        Disconnect from VPN.

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        # Common disconnect commands for different VPN clients
        disconnect_commands = [
            "protonvpn-cli d",
            "nordvpn disconnect",
            "expressvpn disconnect",
            "killall openvpn",
        ]

        for cmd in disconnect_commands:
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    logger.info(f"VPN disconnected using: {cmd}")
                    return True
            except Exception:
                continue

        logger.warning("Could not disconnect VPN automatically")
        return False

    def status(self) -> str:
        """
        Get VPN connection status.

        Returns:
            Status string
        """
        if not self.enabled:
            return "VPN disabled"

        # Try common status commands
        status_commands = [
            "protonvpn-cli status",
            "nordvpn status",
            "expressvpn status",
        ]

        for cmd in status_commands:
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except Exception:
                continue

        return "VPN status unknown"

    def should_switch(self) -> bool:
        """
        Check if it's time to switch VPN connection.

        Returns:
            True if should switch, False otherwise
        """
        if not self.enabled:
            return False

        self.switch_count += 1
        return self.switch_count % self.switch_frequency == 0

    def switch(self) -> bool:
        """
        Switch to a new VPN connection.

        Returns:
            True if successful, False otherwise
        """
        if not self.should_switch():
            return False

        logger.info("Switching VPN connection...")
        self.disconnect()
        time.sleep(2)
        return self.connect()

    def reset_counter(self):
        """Reset the switch counter."""
        self.switch_count = 0


# Global VPN manager instance
vpn_manager = VPNManager()
