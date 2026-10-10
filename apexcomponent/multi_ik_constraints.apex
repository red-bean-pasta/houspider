limits, success = character.detailAttribValue_Dict("joint_limits")
if not success:
    raise error("Missing detail attribute 'joint_limits' on input character geometry.")

specs: Dict = {}
if "min_flex_angles" in limits.keys():
    specs["*"] = limits
else:
    specs = limits

deg_to_rad = 0.017453292519943295

for pattern in specs.keys():
    chain_limits: Dict = specs[pattern]
    min_flex: FloatArray = chain_limits["min_flex_angles"]
    max_flex: FloatArray = chain_limits["max_flex_angles"]
    min_yaw: FloatArray = chain_limits["min_yaw_angles"]
    max_yaw: FloatArray = chain_limits["max_yaw_angles"]
    rest_flex: FloatArray = chain_limits["rest_flex_angles"]

    solvers = graph.matchNodes(pattern + " & %callback(rig::MultiBoneIK)")

    for solver in solvers:
        properties: Dict = {}

        for i in range(len(min_flex)):
            lo_flex = min_flex[i]
            hi_flex = max_flex[i]
            lo_yaw = min_yaw[i]
            hi_yaw = max_yaw[i]
            cur_rest = rest_flex[i]
            mid_yaw = 0.5 * (lo_yaw + hi_yaw)

            lower = Vector3((cur_rest - hi_flex) * deg_to_rad, (lo_yaw - mid_yaw) * deg_to_rad, -3.141592653589793)
            upper = Vector3((cur_rest - lo_flex) * deg_to_rad, (hi_yaw - mid_yaw) * deg_to_rad, 3.141592653589793)
            restangle = Vector3(0.0, 0.0, 0.0)

            properties[String(i)] = {
                "rotation_lower_limits": lower,
                "rotation_upper_limits": upper,
                "restangle": restangle,
            }

        solver.setParms({"properties": properties})


