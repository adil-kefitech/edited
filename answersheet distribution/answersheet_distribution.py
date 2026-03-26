import ast

import pandas as pd
from cryptography.fernet import Fernet
from django.db import transaction
from django.db.models import Count, F
from django.utils import timezone
from rest_framework import status  # basically sent back status
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView  # normal view can written API data
from river.models import State
from simple_history.utils import bulk_create_with_history

from online_evaluation.serializers import (
    AnswersheetExaminationScheduleSerializer,
    BundleDisTypeSer,
    CampRoleAllocationSerializer,
    QPCourseSerializer,
)
from util.constants import *
from util.models import *

# from util.pagination import *
from util.serializers import ExaminationTypeMasterSerializer


def eligibility_check(first, second, total, flag):
    if (abs(first - second) / total) * 100 > flag:
        return True
    return False


def mark_decrypt(data):
    try:
        #

        with open("pvt_key_me.pem", "r") as privatefile:
            private_key = privatefile.read()
        f = Fernet(private_key.encode())
        decrypted_mark = f.decrypt(
            (str(data[2 : len(data) - 1]).encode())
        ).decode()
        return decrypted_mark
    except:
        return "0.0"


class AnswersheetDistribution(APIView):
    def get(self, request):
        try:
            exam = ExaminationTypeMaster.objects.all()
            examt = ExaminationTypeMasterSerializer(exam, many=True).data

            return format_response(
                True,
                FETCH_SUCCESS_MSG,
                data={"examt": examt},
                status_code=status.HTTP_201_CREATED,
                template_name="answer_sheet_distribution_online.html",
            )
        except Exception as e:
            logger.error(e, exc_info=True)
            return format_response(
                False,
                BAD_GATEWAY,
                {},
                BAD_GATEWAY_ERROR_CODE,
                status_code=status.HTTP_400_BAD_REQUEST,
                template_name="answer_sheet_distribution_online.html",
            )

    @transaction.atomic
    def post(self, request):
        try:
            jsondata = request.data
            ##
            user = request.user
            created_on = timezone.now()
            qpcode = jsondata["qpcode"]
            print("qpcodeqpcode",qpcode)
            camp_rol_allo = jsondata["examiner"]  # camproleallo
            print("camp_rol_allocamp_rol_allocamp_rol_allo",camp_rol_allo)
            # #
            no_of_as = jsondata["no_as"]
            print("no_of_asno_of_asno_of_as",no_of_as)
            course = jsondata["courseid"]
            exam_id = jsondata["examid"]
            print("exam_idexam_idexam_id",exam_id)
            
            distributiontype = jsondata["examinert"]
            pgmcourseid = jsondata["course"]
            print("pgmcourseidpgmcourseidpgmcourseid///",pgmcourseid)

            sequencnumberlist = []
            candidatelist = []

            examiner_evalued_dfms = list(
                ExaminerScannedAnswersheet.objects.filter(
                    examiner_id=camp_rol_allo
                ).values_list("answersheet__dfm__id")
            )
            print("examiner_evalued_dfmsexaminer_evalued_dfms",examiner_evalued_dfms)

            # logger.error("examiner evaluated dfm")
            # logger.error(examiner_evalued_dfms)
            chief_evalued_dfms = list(
                ExaminerScannedAnswersheet.objects.filter(
                    examiner__camp_group__group__name=CHIEF_EXAMINER,
                    status__label=EVALUATED_LABEL,
                    answersheet__exam_schedule__exam=exam_id,
                    answersheet__exam_schedule__programme_semester_course_id=pgmcourseid,
                ).values_list("answersheet__dfm__id")
            )
            print("chief_evalued_dfmschief_evalued_dfmschief_evalued_dfms",chief_evalued_dfms)
            # logger.error("chief evaluated dfm")
            # logger.error(chief_evalued_dfms)
            chief_evalued_dfms = []
            examiner_evalued_dfms = examiner_evalued_dfms + chief_evalued_dfms
            print("examiner_evalued_dfmsexaminer_evalued_dfmsexaminer_evalued_dfms",examiner_evalued_dfms)


            s = State.objects.get(label=ALLOCATED_LABEL)

            scan_as = (
                ScannedAnswersheet.objects.filter(
                    exam_schedule__exam=exam_id,
                    exam_schedule__programme_semester_course_id=pgmcourseid,
                    status_id=ACTIVE_STATE,
                    bundle__qp_code=qpcode,
                )
                .annotate(examiners=Count("examinerscannedanswersheet"))
                .filter(examiners=0)
                .exclude(dfm_id=None)
                .exclude(
                    dfm_id__in=examiner_evalued_dfms,
                    )
            )
            print("scan_asscan_asscan_as",scan_as)

            objcount = scan_as.count()
            print("objcountobjcountobjcount",objcount)
            #

            count = 1
            if objcount:

                for i in scan_as:
                    if count > int(no_of_as):
                        break
                    ##
                    ex_as = ExaminerScannedAnswersheet()
                    ex_as.answersheet = i
                    ex_as.examiner_id = camp_rol_allo
                    ex_as.status = s
                    ex_as.created_by = user
                    ex_as.save()
                    # i.status = s  # revert status to active once evaluation is done !!!!!
                    # i.save()
                    candidatelist.append(i.dfm_id)
                    sequencnumberlist.append(
                        str(count).zfill(3)
                    )  # maybe a problem if allocated twice to one examiner !!!!
                    count += 1
                digi = DigitalFalseNumber.objects.filter(
                    exam_registration_course__student_semester_course__prgm_sem_course=pgmcourseid
                ).first()
                # #
                examregcentmap = ExamRegistrationCentreMapper.objects.filter(
                    exam_registration=digi.exam_registration_course.exam_registration
                ).first()
                examcentercode = examregcentmap.exam_center.code

                exam_center = ExaminationCenter.objects.filter(
                    code=examcentercode
                ).first()
                collegecode = exam_center.College.code
                examcodeobj = Examination.objects.filter(id=exam_id).first()
                examcode = examcodeobj.code
                bundlenameexist = BundleMaster.objects.filter(
                    qp_code=qpcode
                ).last()
                #
                if bundlenameexist is None:
                    print("ifififififiifi")
                    # #
                    sequ = 0
                    digital_false_number = DigitalFalseNumber.objects.filter(
                        id__in=candidatelist
                    ).all()
                    candidate_number_list = [
                        int(
                            x.exam_registration_course.student_semester_course.student_semester.student_details.candidate_code
                        )
                        for x in digital_false_number
                    ]
                    sequ += 1
                    bundlename = "Bundle-" + collegecode + str(sequ).zfill(3)
                    bundlecode = "|".join(
                        [str(qpcode), str(examcentercode), str(sequ).zfill(3)]
                    )  # Qpcode+000!!!!
                    val = "".join(bundlecode.split("|"))
                    packet_code = str(sequ).zfill(3)
                    total_count = len(candidate_number_list)
                    c_code_start_range = min(candidate_number_list)
                    c_code_end_range = max(candidate_number_list)
                    hall_details = "NA"

                    decryptedslipdata = bundlecode
                    with open("pbl_bnd_key.pem", "r") as privatefile:
                        private_key = privatefile.read()

                    bundleAdd = BundleMaster(
                        created_by=user,
                        created_on=created_on,
                        bundle_code=val,
                        total_count=total_count,
                        c_code_start_range=c_code_start_range,
                        c_code_end_range=c_code_end_range,
                        hall_details=hall_details,
                        qp_code=qpcode,
                        programme_course_semester_id=pgmcourseid,
                        qr_data="NA",
                        bundle_name=bundlename,
                        status_id=DISTRIBUTED,
                        comments="Bundle created",
                    )
                    bundleAdd.save()
                    bundleid = BundleMaster.objects.latest("id")
                    bundle_id = bundleid.id
                    f = Fernet(private_key.encode())
                    encrypted_message = f.encrypt(str(int(bundle_id)).encode())
                    qrdata = str(encrypted_message)
                    bundleid.qr_data = qrdata
                    bundleid.save()

                    bundleslipadd = BundleSlip(
                        created_by=user,
                        created_on=created_on,
                        bundle=bundleAdd,
                        slip_data=decryptedslipdata,
                        status_id=DISTRIBUTED,
                    )
                    bundleslipadd.save()
                    bundlecandidatemapper = [
                        BundleCandidateMapper(
                            created_by=user,
                            created_on=created_on,
                            bundle=bundleAdd,
                            digital_false_no_id=i,
                            sequence_no=j,
                            status_id=ACTIVE_STATE,
                        )
                        for i, j in zip(candidatelist, sequencnumberlist)
                    ]
                    bundle_cand_objs = bulk_create_with_history(
                        bundlecandidatemapper,
                        BundleCandidateMapper,
                        batch_size=500,
                    )
                    camp_officer = CampRoleAllocation.objects.filter(
                        camp_user=user,
                        camp_group__group__name__in=[CAMP_OFFICER],
                        status_id=ACTIVE_STATE,
                    ).first()
                    bundle_distributiontype = (
                        BundleDistributionType.objects.filter(
                            code=distributiontype
                        ).first()
                    )
                    bundlecamp = BundleCamp(
                        created_by=user,
                        created_on=created_on,
                        bundle=bundleAdd,
                        sub_camp=camp_officer.camp_schedule.sub_camp,
                        camp=camp_officer.camp_schedule.sub_camp.camp,
                        status_id=ALLOCATED,
                    )
                    bundlecamp.save()
                    mark_eval_type = EvaluationType.objects.filter(
                        code=101
                    ).first()
                    bundleexaminer = BundleExaminer(
                        created_by=user,
                        created_on=created_on,
                        bundle_camp=bundlecamp,
                        camp_rol_allo_id=camp_rol_allo,
                        bundle_distribution_type=bundle_distributiontype,
                        evaluation_type=mark_eval_type,
                        status_id=ALLOCATED,
                    )
                    bundleexaminer.save()
                    examiner_false_number = [
                        ExaminerFalseNumber(
                            created_by=user,
                            created_on=created_on,
                            digital_false_no_id=i,
                            camp_rol_allo_id=camp_rol_allo,
                            bundle_distribution_type=bundle_distributiontype,
                            evaluation_type=mark_eval_type,
                            bundle_examiner=bundleexaminer,
                            status_id=PENDING_STATE,
                        )
                        for i in candidatelist
                    ]
                    examiner_false_objs = bulk_create_with_history(
                        examiner_false_number,
                        ExaminerFalseNumber,
                        batch_size=500,
                    )

                else:
                    ##
                    print("elselesewlelseeleselleelslellellel")
                    bundlecodeexist = bundlenameexist.bundle_code
                    seq = bundlecodeexist[-3:]
                    sequ = int(seq)
                    bundlenameexist = bundlenameexist.bundle_name
                    # for bundle in bundlelist:
                    digital_false_number = DigitalFalseNumber.objects.filter(
                        id__in=candidatelist
                    ).all()

                    candidate_number_list = [
                        int(
                            x.exam_registration_course.student_semester_course.student_semester.student_details.candidate_code
                        )
                        for x in digital_false_number
                    ]
                    newbundexist = True
                    while newbundexist :

                        sequ += 1
                        bundlecode = "|".join(
                            [str(qpcode), str(examcentercode), str(sequ).zfill(3)]
                        )
                        val = "".join(bundlecode.split("|"))



                        newbundexist = BundleMaster.objects.filter(bundle_code=val).exists()
                    
                    print("\n BUNDLE CODE----",bundlecode,"VAL ---",val )
                    bundlename = "Bundle-" + collegecode + str(sequ).zfill(3)
                    packet_code = str(sequ).zfill(3)
                    total_count = len(candidate_number_list)
                    c_code_start_range = min(candidate_number_list)
                    c_code_end_range = max(candidate_number_list)
                    hall_details = "NA"
                    stateid = State.objects.filter(label="GENERATED").first()

                    decryptedslipdata = "OEBundle"
                    bundleAdd = BundleMaster(
                        created_by=user,
                        created_on=created_on,
                        bundle_code=val,
                        total_count=total_count,
                        c_code_start_range=c_code_start_range,
                        c_code_end_range=c_code_end_range,
                        hall_details=hall_details,
                        qp_code=qpcode,
                        programme_course_semester_id=pgmcourseid,
                        qr_data="NA",
                        bundle_name=bundlename,
                        status_id=DISTRIBUTED,
                        comments="OEBundle created",
                    )
                    bundleAdd.save()
                    with open("pbl_bnd_key.pem", "r") as privatefile:
                        private_key = privatefile.read()
                    bundleid = BundleMaster.objects.get(id=bundleAdd.id)
                    bundle_id = bundleAdd.id
                    f = Fernet(private_key.encode())
                    encrypted_message = f.encrypt(str(int(bundle_id)).encode())
                    qrdata = str(encrypted_message)
                    bundleid.qr_data = qrdata
                    bundleid.save()

                    bundleslipadd = BundleSlip(
                        created_by=user,
                        created_on=created_on,
                        bundle=bundleAdd,
                        slip_data=decryptedslipdata,
                        status_id=DISTRIBUTED,
                    )
                    bundleslipadd.save()
                    bundlecandidatemapper = [
                        BundleCandidateMapper(
                            created_by=user,
                            created_on=created_on,
                            bundle=bundleAdd,
                            digital_false_no_id=i,
                            sequence_no=j,
                            status_id=ACTIVE_STATE,
                        )
                        for i, j in zip(candidatelist, sequencnumberlist)
                    ]
                    bundle_cand_objs = bulk_create_with_history(
                        bundlecandidatemapper,
                        BundleCandidateMapper,
                        batch_size=500,
                    )
                    camp_officer = CampRoleAllocation.objects.filter(
                        camp_user=user,
                        camp_group__group__name__in=[CAMP_OFFICER],
                        status_id=ACTIVE_STATE,
                    ).first()
                    bundlecamp = BundleCamp(
                        created_by=user,
                        created_on=created_on,
                        bundle=bundleAdd,
                        camp=camp_officer.camp_schedule.sub_camp.camp,
                        sub_camp=camp_officer.camp_schedule.sub_camp,
                        status_id=ALLOCATED,
                    )
                    bundlecamp.save()
                    bundle_distributiontype = (
                        BundleDistributionType.objects.filter(
                            code=distributiontype
                        ).first()
                    )
                    mark_eval_type = EvaluationType.objects.filter(
                        code=101
                    ).first()
                    bundleexaminer = BundleExaminer(
                        created_by=user,
                        created_on=created_on,
                        bundle_camp=bundlecamp,
                        camp_rol_allo_id=camp_rol_allo,
                        bundle_distribution_type=bundle_distributiontype,
                        status_id=ALLOCATED,
                        evaluation_type=mark_eval_type,
                    )
                    bundleexaminer.save()
                    examiner_false_number = [
                        ExaminerFalseNumber(
                            created_by=user,
                            created_on=created_on,
                            digital_false_no_id=i,
                            camp_rol_allo_id=camp_rol_allo,
                            bundle_distribution_type=bundle_distributiontype,
                            evaluation_type=mark_eval_type,
                            bundle_examiner=bundleexaminer,
                            status_id=PENDING_STATE,
                        )
                        for i in candidatelist
                    ]
                    examiner_false_objs = bulk_create_with_history(
                        examiner_false_number,
                        ExaminerFalseNumber,
                        batch_size=500,
                    )

            count = count - 1
            balance_as = objcount - count
            ##

            # #

            return format_response(
                True,
                FETCH_SUCCESS_MSG,
                data={"count": count, "bal": balance_as},
                status_code=status.HTTP_201_CREATED,
                template_name="answer_sheet_distribution_online.html",
            )
        except Exception as e:
            logger.error(e, exc_info=True)
            return format_response(
                False,
                BAD_GATEWAY,
                {},
                BAD_GATEWAY_ERROR_CODE,
                status_code=status.HTTP_400_BAD_REQUEST,
                template_name="answer_sheet_distribution_online.html",
            )


class CourseList(ListAPIView):
    def post(self, request):
        try:

            jsondata = request.data

            qp_code = jsondata["qpcode"]
            print("qp_codeqp_codeqp_code////--/////",qp_code)

            camp_officer = CampRoleAllocation.objects.filter(
                camp_user=request.user,
                camp_group__group__name__in=[CAMP_OFFICER],
                status_id=ACTIVE_STATE,
            ).first()
            print("camp_officercamp_officer//////--///////",camp_officer)

            if camp_officer:


                questionpaper = QuestionPaper.objects.filter(
                    qp_code=qp_code, status_id=ACTIVE_STATE
                ).all()
                print("questionpaperquestionpaperquestionpaper/////",questionpaper)
                # #
                if questionpaper:
                    ##

                    exam = QuestionPaperExamMapper.objects.filter(
                        qp__in=questionpaper
                    ).all()
                    clist = QPCourseSerializer(exam, many=True)
                    print("course list///////123////////-----////////",clist.data)
                    # #
                    return format_response(
                        True,
                        COURSE_FETCH_SUCCESS_MSG,
                        data={"courses": clist.data},
                        status_code=status.HTTP_200_OK,
                        template_name="answer_sheet_distribution_online.html",
                    )
                else:
                    return format_response(
                        False,
                        QP_CODE_NOT_VALID,
                        data={},
                        status_code=status.HTTP_200_OK,
                        template_name="answer_sheet_distribution_online.html",
                    )
            else:
                return format_response(
                    False,
                    CAMP_OFFICER_NOT_ALLOCATED,
                    data={},
                    status_code=status.HTTP_200_OK,
                    template_name="answer_sheet_distribution_online.html",
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


class ExamDetails(ListAPIView):
    def post(self, request):
        try:
            jsondata = request.data
            qp_code = jsondata["qpcode"]
            pgmcourseid = jsondata["course"]
            prg_cours_sem = ProgrammeCourseSemester.objects.get(id=pgmcourseid)
            #
            questionpaper = QuestionPaper.objects.filter(
                qp_code=qp_code,
                qp_pattern__course=prg_cours_sem.course,
                qp_pattern__sub_course=prg_cours_sem.sub_course,
            ).all()
            exam_mapper = QuestionPaperExamMapper.objects.filter(
                qp__in=questionpaper
            ).values_list("exam_id", flat=True)
            #
            exam_obj = QuestionPaperExamMapper.objects.filter(
                qp__in=questionpaper
            ).first()
            exam = exam_obj.exam
            


           
            scn_answ_obj  = ScannedAnswersheet.objects.filter(exam_schedule__exam=exam,exam_schedule__programme_semester_course_id=pgmcourseid,status_id=ACTIVE_STATE,bundle__qp_code=qp_code).all()
            total_papers = scn_answ_obj.count()
            allocated_paper_count = 0

            for scn in scn_answ_obj:

                allocated = ExaminerScannedAnswersheet.objects.filter(answersheet=scn).exists()
                allocated_paper_count += 1


            unallocated = total_papers - allocated_paper_count



            

            exam_sch = ExaminationSchedule.objects.filter(
                exam_id__in=exam_mapper,
                programme_semester_course_id=pgmcourseid,
            ).all()
            #
            exam_sch = ExaminationSchedule.objects.filter(
                exam_id__in=exam_mapper,
                programme_semester_course_id=pgmcourseid,
            ).first()
            #
            #
            # #
            examseri = AnswersheetExaminationScheduleSerializer(exam_sch)
            dtype = BundleDistributionType.objects.all()
            ser = BundleDisTypeSer(dtype, many=True).data
            return format_response(
                True,
                COURSE_FETCH_SUCCESS_MSG,
                data={
                    "examdetails": examseri.data,
                    "exam_id": exam_sch.exam.id,
                    "total_papers":total_papers,
                    "allocated_paper_count": allocated_paper_count,
                    "unallocated": unallocated,
                    "dtype": ser,
                },
                status_code=status.HTTP_200_OK,
                template_name="answer_sheet_distribution_online.html",
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


class ExaminersList(APIView):
    def post(self, request):
        try:
            user = request.user
            jsondata = request.data
            qp_code = jsondata["qpcode"]
            exam_id = jsondata["exam_id"]
            #
            distribution_type = jsondata["examinert"].strip()
            pgmcourseid = jsondata["course"]

            camp_group = Group.objects.filter(name=distribution_type).first()

            prg_cours = ProgrammeCourseSemester.objects.get(id=pgmcourseid)
            #
            sub_camps = (
                CampRoleAllocation.objects.filter(
                    camp_user=user,
                    camp_group__group__name__in=[CAMP_OFFICER],
                    status_id=ACTIVE_STATE,
                )
                .select_related("camp_schedule", "camp_schedule__sub_camp")
                .all()
                .values_list("camp_schedule__sub_camp")
            )
            print("sub_campssub_campssub_camps",sub_camps)
            # #

            camp_sch_course = CampScheduleCourse.objects.filter(
                exam_schedule__exam_id=exam_id,
                exam_schedule__programme_semester_course=prg_cours,
                camp_schedule__sub_camp__in=sub_camps,
            )

            print("camp_sch_coursecamp_sch_course//////",camp_sch_course)

            desig = DesignationHierarchy.objects.filter(
                group=camp_group
            ).first()
            print("desigdesigdesig",desig)

            #
            if camp_sch_course:

                examiner_list = CampRoleAllocation.objects.filter(
                    camp_course__in=camp_sch_course,
                    camp_group=desig,
                    status_id=ACTIVE_STATE,
                )

                examinerlistser = CampRoleAllocationSerializer(
                    examiner_list, many=True
                )

                return format_response(
                    True,
                    EXAMINER_ALLO_MSG,
                    data={"examiner_list": examinerlistser.data},
                    status_code=status.HTTP_200_OK,
                    template_name="answer_sheet_distribution_online.html",
                )
            else:
                return format_response(
                    True,
                    "",
                    data={},
                    status_code=status.HTTP_200_OK,
                    template_name="answer_sheet_distribution_online.html",
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


# class DistributionType(ListAPIView):
#     def post(self,request):
#         try:
#             dtype=BundleDistributionType.objects.all()
#             ser=BundleDisTypeSer(dtype,many=True).data
#             return format_response(True,"",{'dtype':ser},status_code=status.HTTP_200_OK,template_name="answer_sheet_distribution_online.html")
#         except Exception as e:
#             logger.error(e,exc_info=True)
#             return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST)


class AnswersheetDistributionSecond(APIView):
    def get(self, request):
        try:
            exam = ExaminationTypeMaster.objects.all()
            examt = ExaminationTypeMasterSerializer(exam, many=True).data

            return format_response(
                True,
                FETCH_SUCCESS_MSG,
                data={"examt": examt},
                status_code=status.HTTP_201_CREATED,
                template_name="answer_sheet_distribution_online_second.html",
            )
        except Exception as e:
            logger.error(e, exc_info=True)
            return format_response(
                False,
                BAD_GATEWAY,
                {},
                BAD_GATEWAY_ERROR_CODE,
                status_code=status.HTTP_400_BAD_REQUEST,
                template_name="answer_sheet_distribution_online_second.html",
            )

    @transaction.atomic
    def post(self, request):
        try:
            jsondata = request.data
            ##
            user = request.user
            # #
            created_on = timezone.now()
            qpcode = jsondata["qpcode"]
            camp_rol_allo = jsondata["examiner"]  # camproleallo
            # #
            no_of_as = jsondata["no_as"]
            course = jsondata["courseid"]
            exam_id = jsondata["examid"]
            distributiontype = jsondata["examinert"]
            pgmcourseid = jsondata["course"]
            # #
            # #
            # #
            # #
            sequencnumberlist = []
            candidatelist = []
            examiner_evalued_dfms = list(
                ExaminerScannedAnswersheet.objects.filter(
                    examiner_id=camp_rol_allo
                ).values_list("answersheet__dfm__id")
            )

            logger.error("examiner evaluated dfm")
            logger.error(examiner_evalued_dfms)
            chief_evalued_dfms = list(
                ExaminerScannedAnswersheet.objects.filter(
                    examiner__camp_group__group__name=CHIEF_EXAMINER,
                    status__label=EVALUATED_LABEL,
                    answersheet__exam_schedule__exam=exam_id,
                    answersheet__exam_schedule__programme_semester_course_id=pgmcourseid,
                ).values_list("answersheet__dfm__id")
            )
            logger.error("chief evaluated dfm")
            logger.error(chief_evalued_dfms)
            chief_evalued_dfms = []
            examiner_evalued_dfms = examiner_evalued_dfms + chief_evalued_dfms

            s = State.objects.get(label=ALLOCATED_LABEL)

            scan_as = (
                ScannedAnswersheet.objects.filter(
                    exam_schedule__exam=exam_id,
                    exam_schedule__programme_semester_course_id=pgmcourseid,
                    status_id=ACTIVE_STATE,
                )
                .annotate(total=Count("examinerscannedanswersheet"))
                .filter(total=1)
                .exclude(
                    dfm_id__in=examiner_evalued_dfms,
                )
                .order_by("-id")
            )
            # print(scan_as.query)
            #
            objcount = scan_as.count()
            #
            #
            logger.error("scn as")
            logger.error(objcount)
            count = 1
            if objcount:

                for i in scan_as:
                    if count > int(no_of_as):
                        break
                    ##
                    ex_as = ExaminerScannedAnswersheet()
                    ex_as.answersheet = i
                    ex_as.examiner_id = camp_rol_allo
                    ex_as.status = s
                    ex_as.created_by = user
                    ex_as.save()
                    # i.status = s  # revert status to active once evaluation is done !!!!!
                    i.save()
                    candidatelist.append(i.dfm_id)
                    sequencnumberlist.append(
                        str(count).zfill(3)
                    )  # maybe a problem if allocated twice to one examiner !!!!
                    count += 1
                digi = DigitalFalseNumber.objects.filter(
                    exam_registration_course__student_semester_course__prgm_sem_course=pgmcourseid
                ).first()
                # #
                examregcentmap = ExamRegistrationCentreMapper.objects.filter(
                    exam_registration=digi.exam_registration_course.exam_registration
                ).first()
                examcentercode = examregcentmap.exam_center.code

                exam_center = ExaminationCenter.objects.filter(
                    code=examcentercode
                ).first()
                collegecode = exam_center.College.code
                examcodeobj = Examination.objects.filter(id=exam_id).first()
                examcode = examcodeobj.code
                bundlenameexist = BundleMaster.objects.filter(
                    qp_code=qpcode
                ).last()
                #
                if bundlenameexist is None:
                    # #
                    sequ = 0
                    digital_false_number = DigitalFalseNumber.objects.filter(
                        id__in=candidatelist
                    ).all()
                    candidate_number_list = [
                        int(
                            x.exam_registration_course.student_semester_course.student_semester.student_details.candidate_code
                        )
                        for x in digital_false_number
                    ]
                    sequ += 1
                    bundlename = "Bundle-" + collegecode + str(sequ).zfill(3)
                    bundlecode = "|".join(
                        [str(qpcode), str(examcentercode), str(sequ).zfill(3)]
                    )  # Qpcode+000!!!!
                    val = "".join(bundlecode.split("|"))
                    packet_code = str(sequ).zfill(3)
                    total_count = len(candidate_number_list)
                    c_code_start_range = min(candidate_number_list)
                    c_code_end_range = max(candidate_number_list)
                    hall_details = "NA"

                    decryptedslipdata = bundlecode
                    with open("pbl_bnd_key.pem", "r") as privatefile:
                        private_key = privatefile.read()

                    bundleAdd = BundleMaster(
                        created_by=user,
                        created_on=created_on,
                        bundle_code=val,
                        total_count=total_count,
                        c_code_start_range=c_code_start_range,
                        c_code_end_range=c_code_end_range,
                        hall_details=hall_details,
                        qp_code=qpcode,
                        programme_course_semester_id=pgmcourseid,
                        qr_data="NA",
                        bundle_name=bundlename,
                        status_id=DISTRIBUTED,
                        comments="Bundle created",
                    )
                    bundleAdd.save()
                    bundleid = BundleMaster.objects.latest("id")
                    bundle_id = bundleid.id
                    f = Fernet(private_key.encode())
                    encrypted_message = f.encrypt(str(int(bundle_id)).encode())
                    qrdata = str(encrypted_message)
                    bundleid.qr_data = qrdata
                    bundleid.save()

                    bundleslipadd = BundleSlip(
                        created_by=user,
                        created_on=created_on,
                        bundle=bundleAdd,
                        slip_data=decryptedslipdata,
                        status_id=DISTRIBUTED,
                    )
                    bundleslipadd.save()
                    bundlecandidatemapper = [
                        BundleCandidateMapper(
                            created_by=user,
                            created_on=created_on,
                            bundle=bundleAdd,
                            digital_false_no_id=i,
                            sequence_no=j,
                            status_id=ACTIVE_STATE,
                        )
                        for i, j in zip(candidatelist, sequencnumberlist)
                    ]
                    bundle_cand_objs = bulk_create_with_history(
                        bundlecandidatemapper,
                        BundleCandidateMapper,
                        batch_size=500,
                    )
                    camp_officer = CampRoleAllocation.objects.filter(
                        camp_user=user,
                        camp_group__group__name__in=[CAMP_OFFICER],
                        status_id=ACTIVE_STATE,
                    ).first()
                    bundle_distributiontype = (
                        BundleDistributionType.objects.filter(
                            code=distributiontype
                        ).first()
                    )
                    bundlecamp = BundleCamp(
                        created_by=user,
                        created_on=created_on,
                        bundle=bundleAdd,
                        sub_camp=camp_officer.camp_schedule.sub_camp,
                        camp=camp_officer.camp_schedule.sub_camp.camp,
                        status_id=ALLOCATED,
                    )
                    bundlecamp.save()
                    mark_eval_type = EvaluationType.objects.filter(
                        code=102
                    ).first()
                    bundleexaminer = BundleExaminer(
                        created_by=user,
                        created_on=created_on,
                        bundle_camp=bundlecamp,
                        camp_rol_allo_id=camp_rol_allo,
                        bundle_distribution_type=bundle_distributiontype,
                        evaluation_type=mark_eval_type,
                        status_id=ALLOCATED,
                    )
                    bundleexaminer.save()
                    examiner_false_number = [
                        ExaminerFalseNumber(
                            created_by=user,
                            created_on=created_on,
                            digital_false_no_id=i,
                            camp_rol_allo_id=camp_rol_allo,
                            bundle_distribution_type=bundle_distributiontype,
                            evaluation_type=mark_eval_type,
                            bundle_examiner=bundleexaminer,
                            status_id=PENDING_STATE,
                        )
                        for i in candidatelist
                    ]
                    examiner_false_objs = bulk_create_with_history(
                        examiner_false_number,
                        ExaminerFalseNumber,
                        batch_size=500,
                    )

                else:
                    ##
                    bundlecodeexist = bundlenameexist.bundle_code
                    seq = bundlecodeexist[-3:]
                    sequ = int(seq)
                    bundlenameexist = bundlenameexist.bundle_name
                    # for bundle in bundlelist:
                    digital_false_number = DigitalFalseNumber.objects.filter(
                        id__in=candidatelist
                    ).all()

                    candidate_number_list = [
                        int(
                            x.exam_registration_course.student_semester_course.student_semester.student_details.candidate_code
                        )
                        for x in digital_false_number
                    ]
                    newbundexist = True
                    while newbundexist :

                        sequ += 1
                        bundlecode = "|".join(
                            [str(qpcode), str(examcentercode), str(sequ).zfill(3)]
                        )
                        val = "".join(bundlecode.split("|"))



                        newbundexist = BundleMaster.objects.filter(bundle_code=val).exists()

                    bundlename = "Bundle-" + collegecode + str(sequ).zfill(3)
                    packet_code = str(sequ).zfill(3)
                    total_count = len(candidate_number_list)
                    c_code_start_range = min(candidate_number_list)
                    c_code_end_range = max(candidate_number_list)
                    hall_details = "NA"
                    stateid = State.objects.filter(label="GENERATED").first()

                    decryptedslipdata = "OEBundle"
                    bundleAdd = BundleMaster(
                        created_by=user,
                        created_on=created_on,
                        bundle_code=val,
                        total_count=total_count,
                        c_code_start_range=c_code_start_range,
                        c_code_end_range=c_code_end_range,
                        hall_details=hall_details,
                        qp_code=qpcode,
                        programme_course_semester_id=pgmcourseid,
                        qr_data="NA",
                        bundle_name=bundlename,
                        status_id=DISTRIBUTED,
                        comments="OEBundle created",
                    )
                    bundleAdd.save()
                    with open("pbl_bnd_key.pem", "r") as privatefile:
                        private_key = privatefile.read()
                    bundleid = BundleMaster.objects.get(id=bundleAdd.id)
                    bundle_id = bundleAdd.id
                    f = Fernet(private_key.encode())
                    encrypted_message = f.encrypt(str(int(bundle_id)).encode())
                    qrdata = str(encrypted_message)
                    bundleid.qr_data = qrdata
                    bundleid.save()

                    bundleslipadd = BundleSlip(
                        created_by=user,
                        created_on=created_on,
                        bundle=bundleAdd,
                        slip_data=decryptedslipdata,
                        status_id=DISTRIBUTED,
                    )
                    bundleslipadd.save()
                    bundlecandidatemapper = [
                        BundleCandidateMapper(
                            created_by=user,
                            created_on=created_on,
                            bundle=bundleAdd,
                            digital_false_no_id=i,
                            sequence_no=j,
                            status_id=ACTIVE_STATE,
                        )
                        for i, j in zip(candidatelist, sequencnumberlist)
                    ]
                    bundle_cand_objs = bulk_create_with_history(
                        bundlecandidatemapper,
                        BundleCandidateMapper,
                        batch_size=500,
                    )
                    camp_officer = CampRoleAllocation.objects.filter(
                        camp_user=user,
                        camp_group__group__name__in=[CAMP_OFFICER],
                        status_id=ACTIVE_STATE,
                    ).first()
                    bundlecamp = BundleCamp(
                        created_by=user,
                        created_on=created_on,
                        bundle=bundleAdd,
                        camp=camp_officer.camp_schedule.sub_camp.camp,
                        sub_camp=camp_officer.camp_schedule.sub_camp,
                        status_id=ALLOCATED,
                    )
                    bundlecamp.save()
                    bundle_distributiontype = (
                        BundleDistributionType.objects.filter(
                            code=distributiontype
                        ).first()
                    )
                    mark_eval_type = EvaluationType.objects.filter(
                        code=102
                    ).first()
                    bundleexaminer = BundleExaminer(
                        created_by=user,
                        created_on=created_on,
                        bundle_camp=bundlecamp,
                        camp_rol_allo_id=camp_rol_allo,
                        bundle_distribution_type=bundle_distributiontype,
                        status_id=ALLOCATED,
                        evaluation_type=mark_eval_type,
                    )
                    bundleexaminer.save()
                    examiner_false_number = [
                        ExaminerFalseNumber(
                            created_by=user,
                            created_on=created_on,
                            digital_false_no_id=i,
                            camp_rol_allo_id=camp_rol_allo,
                            bundle_distribution_type=bundle_distributiontype,
                            evaluation_type=mark_eval_type,
                            bundle_examiner=bundleexaminer,
                            status_id=PENDING_STATE,
                        )
                        for i in candidatelist
                    ]
                    examiner_false_objs = bulk_create_with_history(
                        examiner_false_number,
                        ExaminerFalseNumber,
                        batch_size=500,
                    )

            count = count - 1
            balance_as = objcount - count
            ##

            # #

            return format_response(
                True,
                FETCH_SUCCESS_MSG,
                data={"count": count, "bal": balance_as},
                status_code=status.HTTP_201_CREATED,
                template_name="answer_sheet_distribution_online_second.html",
            )
        except Exception as e:
            logger.error(e, exc_info=True)
            return format_response(
                False,
                BAD_GATEWAY,
                {},
                BAD_GATEWAY_ERROR_CODE,
                status_code=status.HTTP_400_BAD_REQUEST,
                template_name="answer_sheet_distribution_online_second.html",
            )


class AnswersheetDistributionThird(APIView):
    def get(self, request):
        try:
            exam = ExaminationTypeMaster.objects.all()
            examt = ExaminationTypeMasterSerializer(exam, many=True).data

            return format_response(
                True,
                FETCH_SUCCESS_MSG,
                data={"examt": examt},
                status_code=status.HTTP_201_CREATED,
                template_name="answer_sheet_distribution_online_third.html",
            )
        except Exception as e:
            logger.error(e, exc_info=True)
            return format_response(
                False,
                BAD_GATEWAY,
                {},
                BAD_GATEWAY_ERROR_CODE,
                status_code=status.HTTP_400_BAD_REQUEST,
                template_name="answer_sheet_distribution_online_third.html",
            )

    @transaction.atomic
    def post(self, request):
        try:

            jsondata = request.data
            ##
            user = request.user
            created_on = timezone.now()
            qpcode = jsondata["qpcode"]
            camp_rol_allo = jsondata["examiner"]  # camproleallo
            # #
            no_of_as = jsondata["no_as"]
            # course = jsondata["courseid"]
            
            exam_id = jsondata["examid"]
            distributiontype = jsondata["examinert"]
            pgmcourseid = jsondata["course"]
            courseobj = ProgrammeCourseSemester.objects.filter(id = pgmcourseid).first()
            course = courseobj.course.id


            sequencnumberlist = []
            candidatelist = []

            examiner_evalued_dfms = list(
                ExaminerScannedAnswersheet.objects.filter(
                    examiner_id=camp_rol_allo
                ).values_list("answersheet__dfm__id")
            )
            chief_evalued_dfms = list(
                ExaminerScannedAnswersheet.objects.filter(
                    examiner__camp_group__group__name=CHIEF_EXAMINER,
                    status__label=EVALUATED_LABEL,
                    answersheet__exam_schedule__exam=exam_id,
                    answersheet__exam_schedule__programme_semester_course_id=pgmcourseid,
                ).values_list("answersheet__dfm__id")
            )
            examiner_evalued_dfms = examiner_evalued_dfms + chief_evalued_dfms
            s = State.objects.get(label=ALLOCATED_LABEL)
            crs_id = (
                ProgrammeCourseSemester.objects.filter(id=pgmcourseid)
                .first()
                .course
            )
            scan_as = (
                ScannedAnswersheet.objects.filter(
                    exam_schedule__exam=exam_id,
                    exam_schedule__programme_semester_course_id=pgmcourseid,
                    status_id=ACTIVE_STATE,
                )
                .annotate(total=Count("examinerscannedanswersheet"))
                .filter(total=3)
            )
            print("scan_asscan_asscan_as",scan_as)

            assigned_digital_false_ids = scan_as.values_list(
                "dfm_id", flat=True
            )
            examiner_evalued_dfms = list(examiner_evalued_dfms) + list(
                assigned_digital_false_ids
            )

            # digital_false_ids = (
            #     NextLevelEvaluationEligibleFalseNumber.objects.filter(
            #         qp_code=qpcode,
            #         digital_false_no__exam_registration_course__student_semester_course__prgm_sem_course__course__id =  course,
            #     ).exclude(digital_false_no_id__in=examiner_evalued_dfms)
            # )
            # print("digital_false_idsdigital_false_ids",digital_false_ids)
            # digital_false_ids=ExaminerFalseNumber.objects.filter(digital_false_no_id__in=digital_false_ids.values_list("id",flat=True),evaluation_type_id=3)
            # First get the initial filtered NextLevelEvaluationEligibleFalseNumber
            digital_false_ids = (
                NextLevelEvaluationEligibleFalseNumber.objects.filter(
                    qp_code=qpcode,
                    digital_false_no__exam_registration_course__student_semester_course__prgm_sem_course__course__id=course,
                )
                .exclude(digital_false_no_id__in=examiner_evalued_dfms)
            )

            print("digital_false_idsdigital_false_ids", digital_false_ids.count())

            # Now get the digital_false_no IDs that have ExaminerFalseNumber with evaluation_type_id=3
            # from the already filtered digital_false_ids
            examiner_false_ids = ExaminerFalseNumber.objects.filter(
                digital_false_no_id__in=digital_false_ids.values_list('digital_false_no_id', flat=True),
                evaluation_type_id=3
            ).values_list('digital_false_no_id', flat=True)
            print("examiner_false_idsexaminer_false_idsexaminer_false_idsexaminer_false_ids",examiner_false_ids.count())

            # Finally exclude those IDs from digital_false_ids
            digital_false_ids = digital_false_ids.exclude(digital_false_no_id__in=examiner_false_ids)

            print("Final digital_false_ids", digital_false_ids)
            count = 1
            objcount = digital_false_ids.count()
            print("objcountobjcountobjcount",objcount)
           
            # cors_param_obj = CourseParamsValue.objects.filter(
            #     status_id=ACTIVE_STATE,
            #     course=crs_id,
            #     course_parms_programme_type__course_parms__code=ESA_MARK_CMP_COURSE_PARAM_CODE,
            # ).last()
            # if cors_param_obj:
            #     flag = cors_param_obj.course_parmas_value

            # else:
            #     logger.error("Course param value is not added")
            #     return format_response(
            #         False,
            #         BAD_GATEWAY,
            #         {},
            #         BAD_GATEWAY_ERROR_CODE,
            #         status_code=status.HTTP_400_BAD_REQUEST,
            #         template_name="answer_sheet_distribution_online_third.html",
            #     )

            # course_param_obj = CourseParamsValue.objects.filter(
            #     status_id=ACTIVE_STATE,
            #     course=crs_id,
            #     course_parms_programme_type__course_parms__code=ESA_PASS_MIN,
            # ).last()
            # if course_param_obj:
            #     total = course_param_obj.course_parmas_value
            # else:
            #     total = 100
            # logger.error("Course param value is not added")
            # return format_response(
            #     False,
            #     BAD_GATEWAY,
            #     {},
            #     BAD_GATEWAY_ERROR_CODE,
            #     status_code=status.HTTP_400_BAD_REQUEST,
            #     template_name="answer_sheet_distribution_online_third.html",
            # )
            if objcount:

                for i in digital_false_ids:
                    if count > int(no_of_as):
                        break

                    previous_marks = list(
                        (
                            ScannedAnswersheetMark.objects.filter(
                                exr_as__answersheet__dfm__id=i.digital_false_no_id
                            )
                            .all()
                            .values_list("mark")
                        )
                    )

                    previous_marks.sort()
                    #
                    ans_sheet = ScannedAnswersheet.objects.filter(
                        dfm_id=i.digital_false_no_id
                    ).first()
                    ex_as = ExaminerScannedAnswersheet()
                    ex_as.answersheet = ans_sheet
                    ex_as.examiner_id = camp_rol_allo
                    ex_as.status = s
                    ex_as.created_by = user
                    ex_as.save()
                    # i.status = s  # revert status to active once evaluation is done !!!!!
                    # i.save()
                    candidatelist.append(i.digital_false_no_id)
                    sequencnumberlist.append(
                        str(count).zfill(3)
                    )  # maybe a problem if allocated twice to one examiner !!!!
                    count += 1
                if candidatelist == []:
                    count = count - 1
                    balance_as = objcount - count
                    return format_response(
                        True,
                        FETCH_SUCCESS_MSG,
                        data={"count": count, "bal": balance_as},
                        status_code=status.HTTP_201_CREATED,
                        template_name="answer_sheet_distribution_online_third.html",
                    )

                digi = DigitalFalseNumber.objects.filter(
                    exam_registration_course__student_semester_course__prgm_sem_course=pgmcourseid
                ).first()
                # #
                examregcentmap = ExamRegistrationCentreMapper.objects.filter(
                    exam_registration=digi.exam_registration_course.exam_registration
                ).first()
                examcentercode = examregcentmap.exam_center.code

                exam_center = ExaminationCenter.objects.filter(
                    code=examcentercode
                ).first()
                collegecode = exam_center.College.code
                examcodeobj = Examination.objects.filter(id=exam_id).first()
                examcode = examcodeobj.code
                bundlenameexist = BundleMaster.objects.filter(
                    qp_code=qpcode
                ).last()
                #
                if bundlenameexist is None:
                    # #
                    sequ = 0
                    digital_false_number = DigitalFalseNumber.objects.filter(
                        id__in=candidatelist
                    ).all()
                    candidate_number_list = [
                        int(
                            x.exam_registration_course.student_semester_course.student_semester.student_details.candidate_code
                        )
                        for x in digital_false_number
                    ]
                    sequ += 1
                    bundlename = "Bundle-" + collegecode + str(sequ).zfill(3)
                    bundlecode = "|".join(
                        [str(qpcode), str(examcentercode), str(sequ).zfill(3)]
                    )  # Qpcode+000!!!!
                    val = "".join(bundlecode.split("|"))
                    packet_code = str(sequ).zfill(3)
                    total_count = len(candidate_number_list)
                    c_code_start_range = min(candidate_number_list)
                    c_code_end_range = max(candidate_number_list)
                    hall_details = "NA"

                    decryptedslipdata = bundlecode
                    with open("pbl_bnd_key.pem", "r") as privatefile:
                        private_key = privatefile.read()

                    bundleAdd = BundleMaster(
                        created_by=user,
                        created_on=created_on,
                        bundle_code=val,
                        total_count=total_count,
                        c_code_start_range=c_code_start_range,
                        c_code_end_range=c_code_end_range,
                        hall_details=hall_details,
                        qp_code=qpcode,
                        programme_course_semester_id=pgmcourseid,
                        qr_data="NA",
                        bundle_name=bundlename,
                        status_id=DISTRIBUTED,
                        comments="Bundle created",
                    )
                    bundleAdd.save()
                    bundleid = BundleMaster.objects.latest("id")
                    bundle_id = bundleid.id
                    f = Fernet(private_key.encode())
                    encrypted_message = f.encrypt(str(int(bundle_id)).encode())
                    qrdata = str(encrypted_message)
                    bundleid.qr_data = qrdata
                    bundleid.save()

                    bundleslipadd = BundleSlip(
                        created_by=user,
                        created_on=created_on,
                        bundle=bundleAdd,
                        slip_data=decryptedslipdata,
                        status_id=DISTRIBUTED,
                    )
                    bundleslipadd.save()
                    bundlecandidatemapper = [
                        BundleCandidateMapper(
                            created_by=user,
                            created_on=created_on,
                            bundle=bundleAdd,
                            digital_false_no_id=i,
                            sequence_no=j,
                            status_id=ACTIVE_STATE,
                        )
                        for i, j in zip(candidatelist, sequencnumberlist)
                    ]
                    bundle_cand_objs = bulk_create_with_history(
                        bundlecandidatemapper,
                        BundleCandidateMapper,
                        batch_size=500,
                    )
                    camp_officer = CampRoleAllocation.objects.filter(
                        camp_user=user,
                        camp_group__group__name__in=[CAMP_OFFICER],
                        status_id=ACTIVE_STATE,
                    ).first()
                    bundle_distributiontype = (
                        BundleDistributionType.objects.filter(
                            code=distributiontype
                        ).first()
                    )
                    bundlecamp = BundleCamp(
                        created_by=user,
                        created_on=created_on,
                        bundle=bundleAdd,
                        sub_camp=camp_officer.camp_schedule.sub_camp,
                        camp=camp_officer.camp_schedule.sub_camp.camp,
                        status_id=ALLOCATED,
                    )
                    bundlecamp.save()
                    mark_eval_type = EvaluationType.objects.filter(
                        code=103
                    ).first()
                    bundleexaminer = BundleExaminer(
                        created_by=user,
                        created_on=created_on,
                        bundle_camp=bundlecamp,
                        camp_rol_allo_id=camp_rol_allo,
                        bundle_distribution_type=bundle_distributiontype,
                        evaluation_type=mark_eval_type,
                        status_id=ALLOCATED,
                    )
                    bundleexaminer.save()
                    examiner_false_number = [
                        ExaminerFalseNumber(
                            created_by=user,
                            created_on=created_on,
                            digital_false_no_id=i,
                            camp_rol_allo_id=camp_rol_allo,
                            bundle_distribution_type=bundle_distributiontype,
                            evaluation_type=mark_eval_type,
                            bundle_examiner=bundleexaminer,
                            status_id=PENDING_STATE,
                        )
                        for i in candidatelist
                    ]
                    examiner_false_objs = bulk_create_with_history(
                        examiner_false_number,
                        ExaminerFalseNumber,
                        batch_size=500,
                    )

                else:

                    bundlecodeexist = bundlenameexist.bundle_code
                    seq = bundlecodeexist[-3:]
                    sequ = int(seq)
                    bundlenameexist = bundlenameexist.bundle_name
                    # for bundle in bundlelist:
                    digital_false_number = DigitalFalseNumber.objects.filter(
                        id__in=candidatelist
                    ).all()

                    candidate_number_list = [
                        int(
                            x.exam_registration_course.student_semester_course.student_semester.student_details.candidate_code
                        )
                        for x in digital_false_number
                    ]
                    newbundexist = True
                    while newbundexist :
                        sequ += 1
                        bundlecode = "|".join(
                            [str(qpcode), str(examcentercode), str(sequ).zfill(3)]
                        )
                        val = "".join(bundlecode.split("|"))
                        newbundexist = BundleMaster.objects.filter(bundle_code=val).exists()
                       
                    bundlename = "Bundle-" + collegecode + str(sequ).zfill(3)
                    packet_code = str(sequ).zfill(3)
                    total_count = len(candidate_number_list)
                    c_code_start_range = min(candidate_number_list)
                    c_code_end_range = max(candidate_number_list)
                    hall_details = "NA"
                    stateid = State.objects.filter(label="GENERATED").first()

                    decryptedslipdata = "OEBundle"
                    bundleAdd = BundleMaster(
                        created_by=user,
                        created_on=created_on,
                        bundle_code=val,
                        total_count=total_count,
                        c_code_start_range=c_code_start_range,
                        c_code_end_range=c_code_end_range,
                        hall_details=hall_details,
                        qp_code=qpcode,
                        programme_course_semester_id=pgmcourseid,
                        qr_data="NA",
                        bundle_name=bundlename,
                        status_id=DISTRIBUTED,
                        comments="OEBundle created",
                    )
                    bundleAdd.save()
                    with open("pbl_bnd_key.pem", "r") as privatefile:
                        private_key = privatefile.read()
                    bundleid = BundleMaster.objects.get(id=bundleAdd.id)
                    bundle_id = bundleAdd.id
                    f = Fernet(private_key.encode())
                    encrypted_message = f.encrypt(str(int(bundle_id)).encode())
                    qrdata = str(encrypted_message)
                    bundleid.qr_data = qrdata
                    bundleid.save()

                    bundleslipadd = BundleSlip(
                        created_by=user,
                        created_on=created_on,
                        bundle=bundleAdd,
                        slip_data=decryptedslipdata,
                        status_id=DISTRIBUTED,
                    )
                    bundleslipadd.save()
                    bundlecandidatemapper = [
                        BundleCandidateMapper(
                            created_by=user,
                            created_on=created_on,
                            bundle=bundleAdd,
                            digital_false_no_id=i,
                            sequence_no=j,
                            status_id=ACTIVE_STATE,
                        )
                        for i, j in zip(candidatelist, sequencnumberlist)
                    ]
                    bundle_cand_objs = bulk_create_with_history(
                        bundlecandidatemapper,
                        BundleCandidateMapper,
                        batch_size=500,
                    )
                    camp_officer = CampRoleAllocation.objects.filter(
                        camp_user=user,
                        camp_group__group__name__in=[CAMP_OFFICER],
                        status_id=ACTIVE_STATE,
                    ).first()
                    bundlecamp = BundleCamp(
                        created_by=user,
                        created_on=created_on,
                        bundle=bundleAdd,
                        camp=camp_officer.camp_schedule.sub_camp.camp,
                        sub_camp=camp_officer.camp_schedule.sub_camp,
                        status_id=ALLOCATED,
                    )
                    bundlecamp.save()
                    bundle_distributiontype = (
                        BundleDistributionType.objects.filter(
                            code=distributiontype
                        ).first()
                    )
                    mark_eval_type = EvaluationType.objects.filter(
                        code=103
                    ).first()
                    bundleexaminer = BundleExaminer(
                        created_by=user,
                        created_on=created_on,
                        bundle_camp=bundlecamp,
                        camp_rol_allo_id=camp_rol_allo,
                        bundle_distribution_type=bundle_distributiontype,
                        status_id=ALLOCATED,
                        evaluation_type=mark_eval_type,
                    )
                    bundleexaminer.save()
                    examiner_false_number = [
                        ExaminerFalseNumber(
                            created_by=user,
                            created_on=created_on,
                            digital_false_no_id=i,
                            camp_rol_allo_id=camp_rol_allo,
                            bundle_distribution_type=bundle_distributiontype,
                            evaluation_type=mark_eval_type,
                            bundle_examiner=bundleexaminer,
                            status_id=PENDING_STATE,
                        )
                        for i in candidatelist
                    ]
                    examiner_false_objs = bulk_create_with_history(
                        examiner_false_number,
                        ExaminerFalseNumber,
                        batch_size=500,
                    )

            count = count - 1
            balance_as = objcount - count

            return format_response(
                True,
                FETCH_SUCCESS_MSG,
                data={"count": count, "bal": balance_as},
                status_code=status.HTTP_201_CREATED,
                template_name="answer_sheet_distribution_online_third.html",
            )
        except Exception as e:
            logger.error(e, exc_info=True)
            return format_response(
                False,
                BAD_GATEWAY,
                {},
                BAD_GATEWAY_ERROR_CODE,
                status_code=status.HTTP_400_BAD_REQUEST,
                template_name="answer_sheet_distribution_online_third.html",
            )
