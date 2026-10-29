"""Send script commands to Aladin Desktop through a SAMP hub (pyvo.samp)."""

from pyvo.samp import SAMPHubError, SAMPIntegratedClient

MTYPE = "script.aladin.send"

HOW_TO_ENABLE = (
    "No SAMP hub is running. To enable it:\n"
    "1. Open Aladin Desktop (java -jar Aladin.jar, or the installed launcher).\n"
    "2. Aladin starts its own internal SAMP hub automatically if none exists. If it does not, "
    "use the 'Interop' menu -> 'Start internal SAMP hub' / 'Connect to SAMP hub'.\n"
    "3. The SAMP icon at the bottom of the Aladin window turns green when connected.\n"
    "4. Alternatively run a standalone hub (e.g. TOPCAT, or `samp_hub` from astropy) and "
    "connect Aladin to it from the 'Interop' menu.\n"
    "Then call aladin_send again."
)

NO_REPLY = (
    "Aladin received the script but did not confirm within {timeout} s. It may still be running it: "
    "commands that load surveys or catalogues, or resolve object names, wait for the CDS servers. "
    "Check the Aladin window; local commands such as 'zoom' or 'grid on' confirm at once."
)


def send(commands: str, timeout_s: int = 20) -> dict:
    """Run an Aladin script and wait for Aladin's reply (samp.status) up to timeout_s seconds."""
    client = SAMPIntegratedClient(name="aladin-mcp", description="Claude MCP server for Aladin",
                                  callable=False)
    try:
        client.connect()
    except (SAMPHubError, ConnectionError, OSError) as exc:
        return {"enviado": False, "mensaje": HOW_TO_ENABLE, "detalle": str(exc)}
    try:
        targets = client.get_subscribed_clients(MTYPE)
        if not targets:
            return {"enviado": False,
                    "mensaje": "A SAMP hub is running but no client accepts "
                               f"'{MTYPE}'. Open Aladin Desktop and connect it to the hub "
                               "(Interop menu)."}
        message = {"samp.mtype": MTYPE, "samp.params": {"script": commands}}
        replies = []
        for client_id in targets:
            name = client.get_metadata(client_id).get("samp.name", client_id)
            try:
                reply = client.call_and_wait(client_id, message, str(timeout_s))
            except Exception as exc:  # SAMPProxyError on timeout
                if "timeout" not in str(exc).lower():
                    raise
                replies.append({"destinatario": name, "confirmado": False,
                                "mensaje": NO_REPLY.format(timeout=timeout_s)})
                continue
            status = reply.get("samp.status")
            replies.append({
                "destinatario": name,
                "confirmado": status == "samp.ok",
                "estado": status,
                "resultado": (reply.get("samp.result") or {}).get("script.result") or None,
                "error": (reply.get("samp.error") or {}).get("samp.errortxt"),
            })
        return {"enviado": True, "script": commands, "respuestas": replies}
    finally:
        client.disconnect()
