# import json

import ast
import json
from django.db.models import Prefetch
from django.utils import timezone
from iteration_utilities import unique_everseen
from venv import create

# from numpy import delete
from rest_framework import status  # basically sent back status
from rest_framework.generics import ListAPIView
from river.models import State
from simple_history.utils import bulk_create_with_history,bulk_update_with_history
from academic.serializers import (
    AcademicCourseSerializer,
    AcademicProgrammeSemesterListSerializers,
    CollegeDistrictSerializer,
    CollegeProgramSerializer,
    CollegeTypeSerializer,
    SubsectionProgramGroupSerializer,
    SubsectionProgramSerializer,
    CollegenewDistrictSerializer,
)
from util.constants import *

from util.models import *
   
from util.serializers import (
    ProgrammeSerializers,
    ProgrammeTypeMasterSerializers,
    UniversityRegulationSchemeProgrammeNewSerializer,
)


class ExtcordDistrict(ListAPIView):
    """Course Mapping class view."""

    def get(self, request):
        try:

            user = request.user

            

            college_obj = AffiliatedCollege.objects.select_related(
                "district"
            ).all()
            districts = CollegeDistrictSerializer(college_obj, many=True).data
            districts = list(unique_everseen(districts))
            clg_type_obj = CollegeTypeMaster.objects.all()
            clg_types = CollegeTypeSerializer(clg_type_obj, many=True).data
            clg_types = list(unique_everseen(clg_types))
            return format_response(
                True,
                PROGRAMME_CATEGORY_FETCH_SUCCESS_MSG,
                data={
                    
                    "districts": districts,
                    
                    
                },
                status_code=status.HTTP_200_OK,
                template_name="extcordallocation.html",
            )
        except Exception as e:
            print(e)
            logger.error(e, exc_info=True)
            return format_response(
                False,
                BAD_GATEWAY,
                {},
                BAD_GATEWAY_ERROR_CODE,
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class ExtcordFetch(ListAPIView):
    def post(self, request):
        try:
            jsondata = request.data
            search_id = jsondata["search_id"]
            print("////////",search_id)

            userobj = None

            if "@" in search_id:  # Check if it's an email
                userobj = User.objects.filter(email=str(search_id)).first()
                
            else:  # Check if it's a beneficiary ID (contains only digits)
                
                usernameobj = TeacherBase.objects.filter(beneficiary_id=str(search_id)).first()
                userobj = User.objects.filter(id=usernameobj.user_id).first()
                
            if userobj:
                usernameobj = User.objects.filter(id=userobj.id).first()
                
                teachusr=usernameobj.id
                
                roleobj=userobj.groups.all()
                role=[]
                for desig in roleobj:
                    desigobj=Group.objects.filter(id=desig.id).first()
                    designme=desigobj.name
                    role.append(designme)
                teachobj=TeacherBase.objects.filter(user_id=userobj.id).first()
                
                collteachobj=CollegeTeacher.objects.filter(teacher_id=teachobj.id).first().college_id
                
                collobjects=AffiliatedCollege.objects.filter(id=collteachobj).first()
                collobj=collobjects.name
                

                mob_no = UserProfiles.objects.filter(user_id=userobj.id).first()
                mail_id = usernameobj.email
                mobile = mob_no.mobile_number
                username=usernameobj.username
                first_name = usernameobj.first_name
                last_name = usernameobj.last_name
                fullname = f"{first_name} {last_name}"
                return format_response(True,data={"fullname": fullname,"mail_id": mail_id,"collobj":collobj,"username":username},status_code=status.HTTP_201_CREATED,template_name='extcordallocation.html')

               
            else:
                return format_response({"message": "User not found"}, status=status.HTTP_NOT_FOUND)
        except Exception as e:
            return format_response(
                {"message": "An error occurred"},
                status=status.HTTP_400_BAD_REQUEST
            )


class ExtcordCollegesFetch(ListAPIView):
    def post(self, request):
        try:

            user = request.user
            user_id = request.data.get("user")

            if "@" in user_id:  # Check if it's an email
                userobj = User.objects.filter(email=str(user_id)).first()
                
            else:  # Check if it's a beneficiary ID (contains only digits)
                
                usernameobj = TeacherBase.objects.filter(beneficiary_id=str(user_id)).first()
                userobj = User.objects.filter(id=usernameobj.user_id).first()
                
            if userobj:
                usernameobj = User.objects.filter(id=userobj.id).first()
          
            extteachobj=ExtTeacherAllocation.objects.filter(user_id=usernameobj.id).all()
            college=[]
            for extteach in extteachobj:
                college_id=extteach.college_id
                college.append(college_id)
            
            clg_prgms=AffiliatedCollege.objects.filter(id__in=college).all()
               
            clgs = CollegenewDistrictSerializer(clg_prgms, many=True).data
            clgs = unique_everseen(clgs)
            return format_response(
                True,
                PROGRAMME_CATEGORY_FETCH_SUCCESS_MSG,
                data={"colleges": clgs},
                status_code=status.HTTP_200_OK,
                template_name="extcordallocation.html",
            )
        except Exception as e:
            logger.error(e, exc_info=True)
            return format_response(
                False,
                BAD_GATEWAY,
                {},
                BAD_GATEWAY_ERROR_CODE,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
class ExtcordWiseCollegesFetch(ListAPIView):
    def post(self, request):
        try:

            user = request.user
            prgm = request.data.get("prgm")
            district_id = request.data.get("district")
            college_code = request.data.get("collge_code")
          

            
            state = State.objects.get(label='ACTIVE')
            clg_prgms = CollegeProgramme.objects.select_related(
                "programme",
                "college_department__college",
                "college_department__college__district",
            ).all()
            if prgm:
                clg_prgms = clg_prgms.filter(programme_id=prgm,status_id=state.id).all()
            if district_id:
                clg_prgms = clg_prgms.filter(
                    college_department__college__district_id=district_id
                ).all()
            if college_code:
                clg_prgms = clg_prgms.filter(
                    college_department__college__code=college_code
                ).all()
                print("///////",clg_prgms)
                

            # if college_type_id:
            #     clg_prgms = clg_prgms.filter(
            #         college_department__college__college_type_id=college_type_id
            #     ).all()
               
            clgs = CollegeProgramSerializer(clg_prgms, many=True).data
            clgs = unique_everseen(clgs)
            return format_response(
                True,
                PROGRAMME_CATEGORY_FETCH_SUCCESS_MSG,
                data={"colleges": clgs},
                status_code=status.HTTP_200_OK,
                template_name="extcordallocation.html",
            )
        except Exception as e:
            logger.error(e, exc_info=True)
            return format_response(
                False,
                BAD_GATEWAY,
                {},
                BAD_GATEWAY_ERROR_CODE,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
class ExtcordUpload(ListAPIView):
    
    def post(self, request):
        try:
            college_list = request.data.get('collegelist', [])
            username = request.data.get("user")
            user = request.user
            created_by = user
            created_on = timezone.now()
            userobj = None

            if "@" in username:  # Check if it's an email
                userobj = User.objects.filter(email=str(username)).first()
                
            else:  # Check if it's a beneficiary ID (contains only digits)
                
                usernameobj = TeacherBase.objects.filter(beneficiary_id=str(username)).first()
                userobj = User.objects.filter(id=usernameobj.user_id).first()
                
            if userobj:
                usernameobj = User.objects.filter(id=userobj.id).first()
            saved_colleges = []

            for college_code in college_list:
                collobj = AffiliatedCollege.objects.filter(code=college_code).first()

                if collobj:
                    extteachobjcheck = ExtTeacherAllocation.objects.filter(user_id=userobj.id, college_id=collobj.id).first()
                    print("///////",extteachobjcheck)
                    if  extteachobjcheck==None:
                        userobj.groups.add(50)

                        saved_colleges.append(ExtTeacherAllocation(
                            created_on=created_on,
                            created_by=created_by,
                            college_id=collobj.id,
                            user_id=userobj.id,
                            status_id=80
                        ))
                        
                  
                        

            if saved_colleges:
                ExtTeacherAllocation.objects.bulk_create(saved_colleges)

                return format_response(True, COORDINATOR_SUCCSS_MSG, status_code=status.HTTP_200_OK, template_name='extcordallocation.html')
            else:
                return format_response({"success": False, "message": COLLEGE_ALREADY_UPLOADED}, status=status.HTTP_200_OK, template_name="extcordallocation.html",)

        except Exception as e:
            print(e)
            return format_response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# class ExtcordDelete(ListAPIView):
#     def post(self, request):
#         try:
#             user = request.user
          
#             today = timezone.now()
#             code = request.data.get('code')
#             dept = request.data.get("dept")
           
#             collobj= AffiliatedCollege.objects.filter(code=code).first()
           

#             deptobj=CollegeDepartment.objects.filter(college_id=collobj,department_id=dept).first()
           
#             state = State.objects.get(label='DELETE')
            
#             prgm = request.data.get("prgm")
           
#             collprgobj = CollegeProgramme.objects.filter(college_department_id=deptobj, programme_id=prgm).first()
           
#             collbatchexistance=CollegeBatchProgramme.objects.filter(college_programm_id=collprgobj).exists()
           
#             collteachexistance=CollegeTeacherProgramme.objects.filter(college_programm_id=collprgobj).exists()
           
#             if not collbatchexistance and not collteachexistance:
                
#                 deleted_count= CollegeProgramme.objects.filter(college_department_id=deptobj, programme_id=prgm).update(status_id=state.id)
              
#                 if deleted_count>0:
#                     return format_response(
#                         True,
#                         "Successfully Deleted",
#                         data={"success":True},
#                         status_code=status.HTTP_200_OK,
#                         template_name="college_programme_mapping.html",
#                     )
                

#         except Exception as e:
#             # Handle exceptions appropriately
#             return format_response(False, str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
       
    



