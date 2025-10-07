import matplotlib.pyplot as plt
import numpy as np
import datetime as dt

times = [dt.datetime.now() - dt.timedelta(minutes=60 - i) for i in range(60)]

sap_success_rate = 90 + np.random.randn(60) * 3  

queue_depth = np.abs(np.random.normal(50, 20, 60)).astype(int)
queue_depth[45:50] += 100  

dlq_count = np.zeros(60)
dlq_count[48:52] = [1, 3, 5, 2] 


worker_latency = np.abs(np.random.normal(2, 0.5, 60))
worker_latency[45:50] += 2  


gateway_latency = np.abs(np.random.normal(120, 20, 60))
gateway_latency[20:25] += 80

sap_health = 90 + np.random.randn(60) * 3  


fig, axs = plt.subplots(3, 2, figsize=(12, 8))
fig.suptitle("Observability Dashboard", fontsize=16, fontweight='bold')

axs[0, 0].plot(times, sap_success_rate, color='green')
axs[0, 0].set_title("SAP Success Rate (%)")
axs[0, 0].set_ylim(70, 100)
axs[0, 0].grid(True, linestyle='--', alpha=0.6)
axs[0, 0].axhline(80, color='red', linestyle='--', label='Alert Threshold')
axs[0, 0].legend(loc='lower center')

axs[0, 1].plot(times, queue_depth, color='orange')
axs[0, 1].set_title("Queue Depth (Messages)")
axs[0, 1].set_ylim(0, max(queue_depth) + 50)
axs[0, 1].grid(True, linestyle='--', alpha=0.6)
axs[0, 1].axhline(200, color='red', linestyle='--', label='Alert Threshold')
axs[0, 1].legend(loc='upper center')


axs[1, 0].plot(times, dlq_count, color='cyan')
axs[1, 0].set_title("DLQ Message Count")
axs[1, 0].grid(True, linestyle='--', alpha=0.6)
axs[1, 0].axhline(1, color='red', linestyle='--', label='Alert Threshold')
axs[1, 0].legend(loc='upper left')

axs[2, 0].plot(times, gateway_latency, color='purple')
axs[2, 0].set_title("Gateway Latency (ms)")
axs[2, 0].grid(True, linestyle='--', alpha=0.6)
axs[2, 0].axhline(250, color='red', linestyle='--', label='Alert Threshold')
axs[2, 0].legend(loc='upper left')

axs[1, 1].plot(times, sap_health, color='gray')
axs[1, 1].set_title("SAP Health (%)")
axs[1, 1].set_ylim(70, 100)
axs[1, 1].grid(True, linestyle='--', alpha=0.6)
axs[1, 1].axhline(80, color='red', linestyle='--', label='Alert Threshold')
axs[1, 1].legend(loc='lower center')

plt.delaxes(axs[2,1])

plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.subplots_adjust(hspace=0.5)
plt.show()
