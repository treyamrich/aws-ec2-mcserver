"""Tests for handler layers — DiscordHandler and K8sHTTPHandler (HTTP)."""

from email.message import Message
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from conftest import SAMPLE_POD_TEMPLATE
from core.service import StartResult, StartOutcome, StopResult, StatusResult, IpResult
from core.state import RunState
from discord_app.handler import DiscordHandler
from k8s import PodTemplate

# http_server.py calls get_service() at module level. Patch PodTemplate.from_file
# so KubernetesService.__init__ doesn't try to read a real file.
with patch.object(PodTemplate, "from_file", return_value=PodTemplate(SAMPLE_POD_TEMPLATE)):
    from http_server import K8sHTTPHandler
import http_server


# ---------------------------------------------------------------------------
# DiscordHandler
# ---------------------------------------------------------------------------


class TestDiscordHandler:

    @pytest.fixture
    def mock_service(self):
        return MagicMock()

    @pytest.fixture
    def discord_handler(self, mock_bot, mock_service):
        with patch("discord_app.handler.get_service", return_value=mock_service):
            handler = DiscordHandler(mock_bot)
        return handler

    # -- start ---------------------------------------------------------------

    @pytest.mark.asyncio
    @patch("discord_app.handler.state_manager")
    async def test_start_sends_embed_on_started(
        self, mock_state, discord_handler, mock_service, mock_ctx
    ):
        mock_service.start.return_value = StartResult(StartOutcome.STARTED)

        await discord_handler.start(mock_ctx)

        # _finalize_discord_start responds with embed
        mock_ctx.respond.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_responds_already_running(
        self, discord_handler, mock_service, mock_ctx
    ):
        mock_service.start.return_value = StartResult(StartOutcome.ALREADY_RUNNING)

        await discord_handler.start(mock_ctx)

        mock_ctx.respond.assert_called_once()
        assert "already running" in str(mock_ctx.respond.call_args).lower()

    @pytest.mark.asyncio
    async def test_start_responds_already_starting(
        self, discord_handler, mock_service, mock_ctx
    ):
        mock_service.start.return_value = StartResult(StartOutcome.ALREADY_STARTING)

        await discord_handler.start(mock_ctx)

        mock_ctx.respond.assert_called_once()
        assert "already starting" in str(mock_ctx.respond.call_args).lower()

    @pytest.mark.asyncio
    async def test_start_responds_failed(
        self, discord_handler, mock_service, mock_ctx
    ):
        mock_service.start.return_value = StartResult(StartOutcome.FAILED)

        await discord_handler.start(mock_ctx)

        mock_ctx.respond.assert_called_once()
        assert "failed" in str(mock_ctx.respond.call_args).lower() or "cry" in str(mock_ctx.respond.call_args).lower()

    @pytest.mark.asyncio
    async def test_start_responds_error(
        self, discord_handler, mock_service, mock_ctx
    ):
        mock_service.start.return_value = StartResult(StartOutcome.ERROR, "something broke")

        await discord_handler.start(mock_ctx)

        mock_ctx.respond.assert_called_once()
        assert "error" in str(mock_ctx.respond.call_args).lower()

    @pytest.mark.asyncio
    async def test_start_responds_connection_error(
        self, discord_handler, mock_service, mock_ctx
    ):
        mock_service.start.return_value = StartResult(
            StartOutcome.ERROR,
            "[Errno 8] nodename nor servname provided, or not known"
        )

        await discord_handler.start(mock_ctx)

        mock_ctx.respond.assert_called_once()
        assert "could not connect" in str(mock_ctx.respond.call_args).lower()

    # -- ip ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_ip_responds_with_message(
        self, discord_handler, mock_service, mock_ctx
    ):
        mock_service.ip.return_value = IpResult(ip="1.2.3.4", message="IP is 1.2.3.4")

        await discord_handler.ip(mock_ctx)

        mock_ctx.respond.assert_called_once()
        assert "1.2.3.4" in str(mock_ctx.respond.call_args)

    @pytest.mark.asyncio
    async def test_ip_responds_kubernetes(
        self, discord_handler, mock_service, mock_ctx
    ):
        mock_service.ip.return_value = IpResult(
            ip=None,
            message="Server is hosted on Kubernetes. Use the server address to connect."
        )

        await discord_handler.ip(mock_ctx)

        mock_ctx.respond.assert_called_once()
        assert "kubernetes" in str(mock_ctx.respond.call_args).lower()

    # -- ping ----------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_ping(self, discord_handler, mock_ctx):
        await discord_handler.ping(mock_ctx)

        mock_ctx.respond.assert_called_once()
        assert "pong" in str(mock_ctx.respond.call_args).lower()

    # -- status --------------------------------------------------------------

    @pytest.mark.asyncio
    @patch("discord_app.handler.embed")
    async def test_status(self, mock_embed, discord_handler, mock_ctx):
        mock_embed.server_status.return_value = MagicMock()

        await discord_handler.status(mock_ctx)

        mock_ctx.respond.assert_called_once()


# ---------------------------------------------------------------------------
# K8sHTTPHandler (HTTP server)
# ---------------------------------------------------------------------------


class TestK8sHTTPHandler:

    @pytest.fixture
    def mock_service(self):
        return MagicMock()

    def _make_handler(self, path, token="test-token", api_token="test-token"):
        """Create a K8sHTTPHandler ready for do_GET without going through __init__."""
        h = K8sHTTPHandler.__new__(K8sHTTPHandler)
        h.path = path
        h._respond = MagicMock()
        headers = Message()
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        h.headers = headers
        return h

    # -- auth ----------------------------------------------------------------

    def test_auth_valid_token(self, mock_service):
        with patch.object(http_server, "service", mock_service), \
             patch.object(http_server, "API_TOKEN", "test-token"):
            mock_service.stop.return_value = StopResult(success=True)
            h = self._make_handler("/k8s/stop", token="test-token")
            h.do_GET()

        h._respond.assert_called_once_with(200, {"action": "deleted", "success": True})

    def test_auth_invalid_token(self, mock_service):
        with patch.object(http_server, "service", mock_service), \
             patch.object(http_server, "API_TOKEN", "test-token"):
            h = self._make_handler("/k8s/stop", token="wrong-token")
            h.do_GET()

        h._respond.assert_called_once_with(401, {"error": "Unauthorized"})
        mock_service.stop.assert_not_called()

    def test_auth_no_header(self, mock_service):
        with patch.object(http_server, "service", mock_service), \
             patch.object(http_server, "API_TOKEN", "test-token"):
            h = self._make_handler("/k8s/stop", token=None)
            h.do_GET()

        h._respond.assert_called_once_with(401, {"error": "Unauthorized"})

    def test_auth_disabled_when_no_api_token(self, mock_service):
        with patch.object(http_server, "service", mock_service), \
             patch.object(http_server, "API_TOKEN", None):
            mock_service.stop.return_value = StopResult(success=True)
            h = self._make_handler("/k8s/stop", token=None)
            h.do_GET()

        h._respond.assert_called_once_with(200, {"action": "deleted", "success": True})

    # -- routing -------------------------------------------------------------

    def test_not_found(self, mock_service):
        with patch.object(http_server, "service", mock_service), \
             patch.object(http_server, "API_TOKEN", None):
            h = self._make_handler("/unknown")
            h.do_GET()

        status, body = h._respond.call_args.args
        assert status == 404
        assert "error" in body

    def test_trailing_slash_stripped(self, mock_service):
        with patch.object(http_server, "service", mock_service), \
             patch.object(http_server, "API_TOKEN", None):
            mock_service.stop.return_value = StopResult(success=True)
            h = self._make_handler("/k8s/stop/")
            h.do_GET()

        h._respond.assert_called_once_with(200, {"action": "deleted", "success": True})

    # -- start ---------------------------------------------------------------

    def test_start_created(self, mock_service):
        with patch.object(http_server, "service", mock_service), \
             patch.object(http_server, "API_TOKEN", None):
            mock_service.start.return_value = StartResult(StartOutcome.STARTED)
            h = self._make_handler("/k8s/start")
            h.do_GET()

        h._respond.assert_called_once_with(200, {"action": "created", "success": True})

    def test_start_already_running(self, mock_service):
        with patch.object(http_server, "service", mock_service), \
             patch.object(http_server, "API_TOKEN", None):
            mock_service.start.return_value = StartResult(StartOutcome.ALREADY_RUNNING)
            h = self._make_handler("/k8s/start")
            h.do_GET()

        h._respond.assert_called_once_with(200, {"action": "none", "message": "Already running"})

    def test_start_already_starting(self, mock_service):
        with patch.object(http_server, "service", mock_service), \
             patch.object(http_server, "API_TOKEN", None):
            mock_service.start.return_value = StartResult(StartOutcome.ALREADY_STARTING)
            h = self._make_handler("/k8s/start")
            h.do_GET()

        h._respond.assert_called_once_with(200, {"action": "none", "message": "Already starting"})

    def test_start_failed(self, mock_service):
        with patch.object(http_server, "service", mock_service), \
             patch.object(http_server, "API_TOKEN", None):
            mock_service.start.return_value = StartResult(StartOutcome.FAILED, "pod creation failed")
            h = self._make_handler("/k8s/start")
            h.do_GET()

        status, body = h._respond.call_args.args
        assert status == 500
        assert body["success"] is False

    def test_start_error(self, mock_service):
        with patch.object(http_server, "service", mock_service), \
             patch.object(http_server, "API_TOKEN", None):
            mock_service.start.return_value = StartResult(StartOutcome.ERROR, "k8s API down")
            h = self._make_handler("/k8s/start")
            h.do_GET()

        status, body = h._respond.call_args.args
        assert status == 500
        assert body["action"] == "error"
        assert "k8s API down" in body["message"]

    # -- stop ----------------------------------------------------------------

    def test_stop_success(self, mock_service):
        with patch.object(http_server, "service", mock_service), \
             patch.object(http_server, "API_TOKEN", None):
            mock_service.stop.return_value = StopResult(success=True)
            h = self._make_handler("/k8s/stop")
            h.do_GET()

        h._respond.assert_called_once_with(200, {"action": "deleted", "success": True})

    def test_stop_failure(self, mock_service):
        with patch.object(http_server, "service", mock_service), \
             patch.object(http_server, "API_TOKEN", None):
            mock_service.stop.return_value = StopResult(success=False)
            h = self._make_handler("/k8s/stop")
            h.do_GET()

        h._respond.assert_called_once_with(500, {"action": "deleted", "success": False})

    # -- status --------------------------------------------------------------

    def test_status_not_found(self, mock_service):
        with patch.object(http_server, "service", mock_service), \
             patch.object(http_server, "API_TOKEN", None):
            mock_service.status.return_value = StatusResult(run_state=None, message="not_found")
            h = self._make_handler("/k8s/status")
            h.do_GET()

        h._respond.assert_called_once_with(200, {"status": "not_found"})

    def test_status_running(self, mock_service):
        with patch.object(http_server, "service", mock_service), \
             patch.object(http_server, "API_TOKEN", None):
            mock_service.status.return_value = StatusResult(run_state=RunState.RUNNING, message="running")
            h = self._make_handler("/k8s/status")
            h.do_GET()

        h._respond.assert_called_once_with(200, {"status": "running"})
