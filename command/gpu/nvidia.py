import command.command as command


class NvidiaSMICommand(command.Command):
    def __init__(self):
        self.command = 'nvidia-smi --query-gpu=timestamp,name,pci.bus_id,driver_version,pstate,pcie.link.gen.max,pcie.link.gen.current,temperature.gpu,utilization.gpu,utilization.memory,memory.total,memory.free,memory.used --format=csv,noheader'  # noqa E501
