limits = bindMultiparm()

addToMultiparm(limits, "lower", Vector3())
addToMultiparm(limits, "upper", Vector3())
addToMultiparm(limits, "restangle", Vector3())

solvers = graph.matchNodes("%callback(rig::MultiBoneIK)")

for solver in solvers:
    properties: Dict = {}

    for i in range(len(limits)):
        limit: Dict = limits[i]
        lower: Vector3 = limit["lower#"]
        upper: Vector3 = limit["upper#"]
        restangle: Vector3 = limit["restangle#"]
        properties[String(i)] = {
            "rotation_lower_limits": lower,
            "rotation_upper_limits": upper,
            "restangle": restangle,
        }

    solver.setParms({"properties": properties})
