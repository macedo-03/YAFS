### Handling Messages and User Requests in YAFS (SimPy)

#### Format

- Aplication
  - Modules
    - Messages
    - Transmission

**Example:**
```json
    "id": 0,
    "name": 0,
    "module": [
        {
            "id": 0,
            "name": "0_0",
            "RAM": 3,
            "type": "MODULE"
        },
        {
            "id": 1,
            "name": "0_1",
            "RAM": 1,
            "type": "MODULE"
        }
    ],
    "message": [
        {
            "id": 0,
            "name": "M.USER.APP.0",
            "s": "None",
            "d": "0_0",
            "instructions": 40946,
            "bytes": 3429037
        },
        {
            "id": 1,
            "name": "0_(0-1)",
            "s": "0_0",
            "d": "0_1",
            "instructions": 26102,
            "bytes": 3886038
        }
    ],
    "transmission": [
        {
            "module": "0_0",
            "message_in": "M.USER.APP.0",
            "message_out": "0_(0-1)"
        },
        {
            "module": "0_1",
            "message_in": "0_(0-1)"
        }
    ]

```

#### Message Handling

- **Message Passing**: 
    
    YAFS uses SimPy's event-driven model to handle message passing between fog nodes and modules. 
  
    Messages are passed between modules using SimPy's store mechanism, which acts as a buffer for message exchange.
  
  ```python
  self.consumer_pipes["%s%s%i"%(app_name,module,ides)] = simpy.Store(self.env)
  ```

- **Consumer Modules**: Modules responsible for processing messages (consumer modules) are implemented as SimPy processes. These processes wait for messages to arrive in their designated message queues. Upon receiving a message, the module processes it according to its logic and potentially forwards it to other modules.

  ```python
  def __add_consumer_module(self, ides, app_name, module, register_consumer_msg):
      self.logger.debug("Added_Process - Module Consumer: %s\t#DES:%i" % (module, ides))
      while not self.stop and self.des_process_running[ides]:
          if self.des_process_running[ides]:
              msg = yield self.consumer_pipes["%s%s%i"%(app_name,module,ides)].get()
              # Process the message
              for register in register_consumer_msg:
                  if msg.name == register["message_in"].name:
                      # The message can be treated by this module
                      # Processing the message
                      if not doBefore:
                          service_time = self.__update_node_metrics(app_name, module, msg, ides, type)
                          yield self.env.timeout(service_time)
                          doBefore = True
                      # Transferring the message
                      if register["dist"](**register["param"]):
                          self.__send_message(app_name, msg_out,ides, self.FORWARD_METRIC)
  ```

- **Source Modules**: Source modules, representing sensors or generators of messages, are also implemented as SimPy processes. These modules generate messages based on predefined distributions and enqueue them for processing by consumer modules.

  ```python
  def __deploy_source_module(self, app_name, module, id_node, msg, distribution):
      idDES = self.__get_id_process()
      self.des_process_running[idDES] = True
      self.env.process(self.__add_source_module(idDES, app_name, module, msg, distribution))
      self.alloc_DES[idDES] = id_node
      return idDES
  ```

- **Sink Modules**: Sink modules, representing actuators or endpoints, receive messages from other modules and process them accordingly. Similar to consumer modules, sink modules are implemented as SimPy processes waiting for messages to arrive in their queues.

  ```python
  def __add_sink_module(self, ides, app_name, module):
      self.logger.debug("Added_Process - Module Pure Sink: %s\t#DES:%i" % (module, ides))
      while not self.stop and self.des_process_running[ides]:
          msg = yield self.consumer_pipes["%s%s%i" % (app_name, module, ides)].get()
          service_time = self.__update_node_metrics(app_name, module, msg, ides, type)
          yield self.env.timeout(service_time)
  ```

#### User Requests ???

- **User Interaction**: YAFS allows users to interact with the simulation environment by deploying monitors and controlling the simulation flow. Users can deploy custom monitors and define distribution functions to observe and control the simulation's progress.

  ```python
  def deploy_monitor(self, name, function, distribution, **param):
      idDES = self.__get_id_process()
      self.des_process_running[idDES] = True
      self.env.process(self.__add_monitor(idDES, name, function, distribution, **param))
      return idDES
  ```

- **Deployment**: User-defined monitors and control processes are deployed as SimPy processes within the simulation environment. These processes interact with the simulation's components, such as fog nodes, modules, and messages, to monitor their behavior or influence the simulation flow.

  ```python
  def deploy_app(self, app, placement, selector):
      self.apps[app.name] = app
      self.alloc_module[app.name] = {}
      if not placement.name in self.placement_policy.keys():
          self.placement_policy[placement.name] = {"placement_policy": placement, "apps": []}
          if placement.activation_dist is not None:
              self.env.process(self.__add_placement_process(placement))
      self.placement_policy[placement.name]["apps"].append(app.name)
      self.selector_path[app.name] = selector
  ```

---