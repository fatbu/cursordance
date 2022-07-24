from pygame.math import *
import math

def convert_pos(pos, scale):
    # new_pos = pos + Vector2(1, 1)
    # new_pos *= scale/2
    return Vector2((pos.x+1)*scale/2, (-pos.y+1)*scale/2)

def convert_scalar(val, scale):
    return val*scale/2

def lerp(a, b, c):
    return a+(b-a)*c
     
def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       raise Exception('lines do not intersect')

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y


# https://www.ryanjuckett.com/biarc-interpolation/
def biarc_interpolator(point1, angle1, point2, angle2):
    def z(a, b):
        return a.x*b.y-a.y-b.x

    vector1 = Vector2(1, 0).rotate(angle1)
    vector2 = Vector2(1, 0).rotate(angle2)

    if angle1%180 == angle2%180:
        return False

    p1 = Vector2(point1)
    p2 = Vector2(point2)
    
    intersect = line_intersection((p1, p1+vector1), (p2, p2+vector2))
    
    intersect = Vector2(intersect)

    t1 = (intersect-p1).normalize()
    t2 = (intersect-p2).normalize()

    if t1.magnitude() == 0 or t2.magnitude() == 0:
        return False

    t = t1+t2
    v = p2-p1

    d = 0
    dn = (2*(1-t1.dot(t2)))
    if dn != 0:
        d = (-v.dot(t)+math.sqrt(v.dot(t)*v.dot(t)+2*(1-t1.dot(t2))*v.dot(v)))/dn
    else:
        dn = 4*v.dot(t2)
        d = v.dot(v)/dn
    
    pm = (p1+p2+d*(t1-t2))/2

    n1 = Vector2(-t1.y, t1.x)
    n2 = Vector2(-t2.y, t2.x)
    dn1 = 2*n1.dot(pm-p1)
    dn2 = 2*n2.dot(pm-p2)
    c1 = False
    o1 = False
    if dn1 != 0:
        c1 = p1+n1*(pm-p1).dot(pm-p1)/dn1
        r1 = abs((pm-p1).dot(pm-p1)/dn1)
        op1 = (p1-c1)/r1
        om1 = (pm-c1)/r1
        zval = z(op1, om1)
        if zval > 0:
            o1 = math.degrees(math.acos(op1.dot(om1)))
        else:
            o1 = -math.degrees(math.acos(op1.dot(om1)))
    c2 = False
    o2 = False
    if dn2 != 0:
        c2 = p2+n2*(pm-p2).dot(pm-p2)/dn2
        r2 = abs((pm-p2).dot(pm-p2)/dn2)
        op2 = (p2-c2)/r2
        om2 = (pm-c2)/r2
        zval = z(op2, om2)
        if zval > 0:
            o2 = math.degrees(math.acos(op2.dot(om2)))
        else:
            o2 = -math.degrees(math.acos(op2.dot(om2)))
    ret = {}

    ret['pm'] = tuple(pm)

    if c1:
        ret['c1'] = tuple(c1)
        ret['o1'] = o1
    else:
        ret['c1'] = False
    if c2:
        ret['c2'] = tuple(c2)
        ret['o2'] = o2
    else:
        ret['c2'] = False

    return ret
    
    



# https://stackoverflow.com/a/59582674
def circle_line_segment_intersection(circle_center, circle_radius, pt1, pt2, full_line=True, tangent_tol=1e-9):
    """ Find the points at which a circle intersects a line-segment.  This can happen at 0, 1, or 2 points.

    :param circle_center: The (x, y) location of the circle center
    :param circle_radius: The radius of the circle
    :param pt1: The (x, y) location of the first point of the segment
    :param pt2: The (x, y) location of the second point of the segment
    :param full_line: True to find intersections along full line - not just in the segment.  False will just return intersections within the segment.
    :param tangent_tol: Numerical tolerance at which we decide the intersections are close enough to consider it a tangent
    :return Sequence[Tuple[float, float]]: A list of length 0, 1, or 2, where each element is a point at which the circle intercepts a line segment.

    Note: We follow: http://mathworld.wolfram.com/Circle-LineIntersection.html
    """

    (p1x, p1y), (p2x, p2y), (cx, cy) = pt1, pt2, circle_center
    (x1, y1), (x2, y2) = (p1x - cx, p1y - cy), (p2x - cx, p2y - cy)
    dx, dy = (x2 - x1), (y2 - y1)
    dr = (dx ** 2 + dy ** 2)**.5
    big_d = x1 * y2 - x2 * y1
    discriminant = circle_radius ** 2 * dr ** 2 - big_d ** 2

    if discriminant < 0:  # No intersection between circle and line
        return []
    else:  # There may be 0, 1, or 2 intersections with the segment
        intersections = [
            (cx + (big_d * dy + sign * (-1 if dy < 0 else 1) * dx * discriminant**.5) / dr ** 2,
             cy + (-big_d * dx + sign * abs(dy) * discriminant**.5) / dr ** 2)
            for sign in ((1, -1) if dy < 0 else (-1, 1))]  # This makes sure the order along the segment is correct
        if not full_line:  # If only considering the segment, filter out intersections that do not fall within the segment
            fraction_along_segment = [(xi - p1x) / dx if abs(dx) > abs(dy) else (yi - p1y) / dy for xi, yi in intersections]
            intersections = [pt for pt, frac in zip(intersections, fraction_along_segment) if 0 <= frac <= 1]
        if len(intersections) == 2 and abs(discriminant) <= tangent_tol:  # If line is tangent to circle, return just one point (as both intersections have same location)
            return [intersections[0]]
        else:
            return intersections
