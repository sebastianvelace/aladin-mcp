"""Send script commands to Aladin Desktop through a SAMP hub."""

import warnings

with warnings.catch_warnings():
    # astropy 8 deprecates astropy.samp in favour of pyvo.samp; it still works.
    warnings.simplefilter("ignore")
    from astropy.samp import SAMPHubError, SAMPIntegratedClient

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


def send(commands: str) -> dict:
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
        sent_to = []
        for client_id in targets:
            client.notify(client_id, message)
            meta = client.get_metadata(client_id)
            sent_to.append(meta.get("samp.name", client_id))
        return {"enviado": True, "destinatarios": sent_to, "script": commands}
    finally:
        client.disconnect()
