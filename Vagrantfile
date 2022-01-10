# -*- mode: ruby -*-
# vi: set ft=ruby :


Vagrant.configure(2) do |config|
  config.hostmanager.enabled = true
  config.hostmanager.manage_host = true
  config.hostmanager.manage_guest = true

  config.vm.define "mirrormanager2" do |mirrormanager2|
    mirrormanager2.vm.box_url = "https://download.fedoraproject.org/pub/fedora/linux/releases/35/Cloud/x86_64/images/Fedora-Cloud-Base-Vagrant-35-1.2.x86_64.vagrant-libvirt.box"
    mirrormanager2.vm.box = "f35-cloud-libvirt"
    mirrormanager2.vm.hostname = "mirrormanager2.tinystage.test"

    mirrormanager2.vm.synced_folder ".", "/vagrant", type: "sshfs"


    mirrormanager2.vm.provider :libvirt do |libvirt|
      libvirt.cpus = 2
      libvirt.memory = 2048
    end

    mirrormanager2.vm.provision "ansible" do |ansible|
      ansible.playbook = "devel/ansible/playbook.yml"
      # ansible.config_file = "devel/ansible/ansible.cfg"
      ansible.verbose = true
    end
  end
end
