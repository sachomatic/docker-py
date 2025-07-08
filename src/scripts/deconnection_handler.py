import streamlit.components.v1 as components
from streamlit import context,session_state

# Fonction Python pour appeler le composant
# def set_handler():
#     components.html(r"""
#     <script>
#     console.log("Adding beacon");
#     const hostName = window.location.hostname;
#     const instance_number = location.host.split(":")[1]?.[3] || '1'; // Safe fallback
#     window.addEventListener('beforeunload', function() {
#         const data = JSON.stringify({ instance: instance_number });
#         const blob = new Blob([data], { type: 'application/json' });

#         navigator.sendBeacon(`http://${hostName}:8080/disconnect`, blob);
#     });
#     </script>
#     """)

def set_handler():
    ip = session_state["ip"]
    components.html("""
    <script>
    const port = {};
    const hostName = "{}";""".format(session_state["port"],ip)+"""
    const instance_number = location.host.split(":")[1]?.[3] || '1'; // Safe fallback
    const url = `http://${hostName}:${port}/disconnect`;
    console.log("Adding beacon to", url);

    window.addEventListener("beforeunload", function(e) {
        const data = JSON.stringify({ instance: instance_number });
        const blob = new Blob([data], { type: 'text/plain' });
        console.log("Sending beacon");
        console.log(url);
        navigator.sendBeacon(url, blob);
    }); // ✅ Proper closing
    </script>
    """)
