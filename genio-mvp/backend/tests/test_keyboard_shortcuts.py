"""Tests for keyboard shortcuts system."""
import pytest
from fastapi.testclient import TestClient


class TestKeyboardShortcuts:
    """Test keyboard shortcuts configuration."""

    def test_get_default_shortcuts(self, client: TestClient, test_user: dict):
        """Should return default keyboard shortcuts."""
        response = client.get(
            "/api/v1/shortcuts",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have default Vim-style shortcuts
        assert "navigation" in data
        assert "actions" in data
        assert "application" in data
        
        # Check specific shortcuts
        nav = data["navigation"]
        assert nav["next_item"]["key"] == "j"
        assert nav["prev_item"]["key"] == "k"
        assert nav["go_to_top"]["key"] == "g"
        assert nav["go_to_top"]["double_tap"] == True

    def test_update_shortcut(self, client: TestClient, test_user: dict):
        """Should update a keyboard shortcut."""
        response = client.put(
            "/api/v1/shortcuts/navigation/next_item",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "key": "ArrowDown",
                "modifiers": [],
                "enabled": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "ArrowDown"

    def test_disable_shortcut(self, client: TestClient, test_user: dict):
        """Should disable a keyboard shortcut."""
        response = client.put(
            "/api/v1/shortcuts/navigation/mark_read",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"enabled": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] == False

    def test_reset_shortcuts(self, client: TestClient, test_user: dict):
        """Should reset all shortcuts to defaults."""
        # First modify a shortcut
        client.put(
            "/api/v1/shortcuts/navigation/next_item",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={"key": "n"}
        )
        
        # Then reset
        response = client.post(
            "/api/v1/shortcuts/reset",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        
        # Verify reset
        get_response = client.get(
            "/api/v1/shortcuts",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        data = get_response.json()
        assert data["navigation"]["next_item"]["key"] == "j"

    def test_export_shortcuts(self, client: TestClient, test_user: dict):
        """Should export shortcuts as JSON."""
        response = client.get(
            "/api/v1/shortcuts/export",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "shortcuts" in data

    def test_import_shortcuts(self, client: TestClient, test_user: dict):
        """Should import shortcuts from JSON."""
        shortcuts_config = {
            "version": "1.0",
            "shortcuts": {
                "navigation": {
                    "next_item": {
                        "key": "n",
                        "description": "Next item",
                        "enabled": True
                    }
                }
            }
        }
        
        response = client.post(
            "/api/v1/shortcuts/import",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json=shortcuts_config
        )
        
        assert response.status_code == 200
        
        # Verify import
        get_response = client.get(
            "/api/v1/shortcuts",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        data = get_response.json()
        assert data["navigation"]["next_item"]["key"] == "n"

    def test_shortcut_conflicts(self, client: TestClient, test_user: dict):
        """Should detect and report shortcut conflicts."""
        # Try to set same key for two actions
        response = client.post(
            "/api/v1/shortcuts/validate",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "shortcuts": {
                    "navigation": {
                        "next_item": {"key": "j"},
                        "prev_item": {"key": "j"}  # Conflict!
                    }
                }
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "conflicts" in data
        assert len(data["conflicts"]) > 0

    def test_contextual_shortcuts(self, client: TestClient, test_user: dict):
        """Should support different shortcut contexts."""
        response = client.get(
            "/api/v1/shortcuts?context=reader",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Reader context might have different shortcuts
        assert "reader" in data or "application" in data

    def test_cheatsheet_endpoint(self, client: TestClient, test_user: dict):
        """Should provide cheatsheet of all shortcuts."""
        response = client.get(
            "/api/v1/shortcuts/cheatsheet",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should be formatted for display
        assert isinstance(data, list) or "sections" in data
